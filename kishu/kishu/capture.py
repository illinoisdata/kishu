"""
Capture Python state.

To use the watchdog on target program:
    python kishu/capture.py [watchdog_args] [target_program [args]]

Help:
    python kishu/capture.py -h

Examples:
    python kishu/capture.py examples/target_longrunning.py
    python kishu/capture.py --verbosity=2 examples/target_longrunning.py
    python kishu/capture.py --cpu-sampling-rate=10.0 examples/target_longrunning.py
"""
import argparse
import atexit
import contextlib
import dill as pickle
import gc
import importlib
import multiprocessing
import os
import re
import signal
import sys
import time
import traceback
from importlib.abc import SourceLoader
from importlib.machinery import ModuleSpec
from loguru import logger
from types import CodeType, FrameType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from kishu.delta import StateDelta
from kishu.exceptions import TypeNotSupportedError
from kishu.state import State


"""
Standard Python captures
"""


class StandardPythonCapture:
    @staticmethod
    def capture_state(
        depth: int = 0,
        truncate_at_frame_id: int = -1,
    ) -> Tuple[State, List[bool]]:
        """
        Capture stack of frames starting at the caller location. Return the state and list of
        booleans indicating whether the frame has been captured before.

        Specify depth to capture at deeper (depth < 0) or shallower (depth > 0) frames.

        WARNING: Caller must delete frames to avoid memory leaks.
        """
        raw_frames = None
        try:
            raw_frames, same_frames = StandardPythonCapture._capture_raw_frames(
                depth=depth + 1,
                truncate_at_frame_id=truncate_at_frame_id,
            )
            assert len(raw_frames) == len(same_frames)
            state = State.parse_from(raw_frames)
        finally:
            del raw_frames

        """
        Both state and same_frames have the same length. Each boolean in same_frames is true when
        the frame has been captured through StandardPythonCapture previously. Note that using
        id(frame) is unreliable as the address can (often) be reused.
        """
        return state, same_frames

    @staticmethod
    def _capture_raw_frames(
        depth: int = 0,
        truncate_at_frame_id: int = -1,
    ) -> Tuple[List[FrameType], List[bool]]:
        """
        Capture stack of frames where caller is at depth=0. Return frames and list of boolean
        indicating whether each frame has been seen.

        WARNING: Caller must delete frames to avoid memory leaks.

        Refer to https://docs.python.org/3/library/inspect.html about frame objects.
        """
        raw_frame: Optional[FrameType] = sys._getframe(1)
        assert raw_frame is not None, 'This Python interpreter does not support currentframe.'
        try:
            raw_frames = []
            while raw_frame is not None and id(raw_frame) != truncate_at_frame_id and depth > 0:
                raw_frame = raw_frame.f_back
                depth -= 1
            while raw_frame is not None and id(raw_frame) != truncate_at_frame_id:
                raw_frames.append(raw_frame)
                raw_frame = raw_frame.f_back
        finally:
            del raw_frame
        return raw_frames, StandardPythonCapture._breadcrumb(raw_frames)

    @staticmethod
    def _breadcrumb(raw_frames: List[FrameType]) -> List[bool]:
        same_frames = [raw_frame.f_trace is not None for raw_frame in raw_frames]
        for raw_frame in raw_frames:
            raw_frame.f_trace = StandardPythonCapture._frame_breadcrumb
        return same_frames

    @staticmethod
    def _frame_breadcrumb(frame, event, arg):
        """
        Dummy function installed as a trace to track which frame has been seen.
        """
        pass
        return StandardPythonCapture._frame_breadcrumb


"""
Execute target code and passively periodically capture frames.

Initial structure is inspired by scalene.
"""


class WatchdogArguments(argparse.Namespace):
    def __init__(self) -> None:
        super().__init__()
        self.cpu_sampling_delay = 1.0  # sec
        self.cpu_sampling_rate = 1.0  # sec/sample

        self.capture_delta_file = None  # file path
        self.capture_metrics_file = None  # file path
        self.logger_file = None  # file path

        self.verbosity = 0  # higher = more prints


class WatchdogSignals:
    def __init__(self) -> None:
        assert sys.platform != "win32"
        self.cpu_timer_signal = signal.ITIMER_VIRTUAL
        self.cpu_signal = signal.SIGVTALRM
        self.start_profiling_signal = signal.SIGILL
        self.stop_profiling_signal = signal.SIGBUS
        self.memcpy_signal = signal.SIGPROF
        self.malloc_signal = signal.SIGXCPU
        self.free_signal = signal.SIGXFSZ
        self.interrupt_signal = signal.SIGINT


class WatchdogCaptureMetrics:
    def __init__(self) -> None:
        """
        For experimental purposes only. Should use better measures/counters instead.
        """
        self.columns: Dict[str, List[Any]] = {}

    def record(self, **kwargs: Dict[str, Any]) -> None:
        for key, value in kwargs.items():
            self.columns.setdefault(key, []).append(value)

    def save_to(self, filename: str, delimiter: str = ",", newline: str = "\n"):
        with open(filename, "w") as f:
            for key, values in self.columns.items():
                f.write(key)
                for value in values:
                    f.write(delimiter)
                    f.write(str(value))
                f.write(newline)


class Watchdog:
    """
    A capture management that instruments the target application and calls capture methods.

    Initially, it parses its command-line arguments, setup Python environment for the target, and
    execute the target application.

    Currently, it periodically captures application's state using system alarm clock. This clock
    only tracks Python execution time and ignores those times in extensions.

    It is implemented as a singleton using attributes and static methods to reduce overheads.
      - Class attributes
      - Arguments
      - Signals
      - Signal handlers
      - Explicit imports
      - Capture function (capture_state)
      - Execution (exec_capture)
      - Instrumentation (launch_exec_capture)
    """

    """Class Attributes"""

    # Configuration
    __capture_core = StandardPythonCapture
    __signals = WatchdogSignals()
    __args = WatchdogArguments()

    # Target program metadata
    __program_path: str = ""
    __program_being_profiled: str = ""
    __exec_capture_frame_id: int = -1  # uninitialized

    # State tracking
    __previous_program_state: State = State([])

    # System calls
    __orig_signal = signal.signal
    __orig_setitimer = signal.setitimer
    __orig_siginterrupt = signal.siginterrupt

    # Experimental properties
    __capture_metrics = WatchdogCaptureMetrics()
    __capture_id = 0

    """Class Attributes"""

    @staticmethod
    def parse_args(argv: List[str] = []) -> Tuple[WatchdogArguments, List[str]]:
        defaults = WatchdogArguments()
        parser = argparse.ArgumentParser(
            prog="Watchdog to capture target program's state.",
            allow_abbrev=False,
        )
        parser.add_argument(
            "--cpu-sampling-delay",
            dest="cpu_sampling_delay",
            type=float,
            default=defaults.cpu_sampling_delay,
            help=f"CPU sampling initial delay (default: {defaults.cpu_sampling_rate})",
        )
        parser.add_argument(
            "--cpu-sampling-rate",
            dest="cpu_sampling_rate",
            type=float,
            default=defaults.cpu_sampling_rate,
            help=f"CPU sampling rate (default: {defaults.cpu_sampling_rate})",
        )
        parser.add_argument(
            "--capture-delta-file",
            dest="capture_delta_file",
            type=str,
            default=defaults.capture_delta_file,
            help="Path to save capture delta",
        )
        parser.add_argument(
            "--capture-metrics-file",
            dest="capture_metrics_file",
            type=str,
            default=defaults.capture_metrics_file,
            help="Path to save capture metrics",
        )
        parser.add_argument(
            "--logger-file",
            dest="logger_file",
            type=str,
            default=defaults.logger_file,
            help="Path to log file",
        )
        parser.add_argument(
            "--verbosity",
            dest="verbosity",
            type=int,
            default=defaults.verbosity,
            help=f"Verbosity (higher for more logs, default: {defaults.verbosity})",
        )
        args, left = parser.parse_known_args(args=argv)
        args = cast(WatchdogArguments, args)
        return args, left

    @staticmethod
    def process_args(args: WatchdogArguments) -> None:
        Watchdog.__args = args

    """Signals"""

    @staticmethod
    def _enable_signals() -> None:
        assert sys.platform != "win32"
        Watchdog.__orig_signal(
            Watchdog.__signals.cpu_signal,
            Watchdog._cpu_signal_handler,
        )
        Watchdog._set_alarm(Watchdog.__args.cpu_sampling_delay)

    @staticmethod
    def _set_alarm(duration_s: float) -> None:
        Watchdog.__orig_setitimer(
            Watchdog.__signals.cpu_timer_signal,
            duration_s,
        )

    @staticmethod
    def _disable_signals() -> None:
        assert sys.platform != "win32"
        Watchdog.__orig_setitimer(Watchdog.__signals.cpu_timer_signal, 0)

    @staticmethod
    def start() -> None:
        Watchdog._enable_signals()

    @staticmethod
    def stop() -> None:
        Watchdog._disable_signals()

    """Signal Handlers"""

    @staticmethod
    def _exit_handler() -> None:
        Watchdog.stop()

    @staticmethod
    def _interruption_handler(
        signum: Union[
            Callable[[signal.Signals, FrameType], None],
            int,
            signal.Handlers,
            None,
        ],
        this_frame: Optional[FrameType],
    ) -> None:
        raise KeyboardInterrupt

    @staticmethod
    def _cpu_signal_handler(
        signum: Union[
            Callable[[signal.Signals, FrameType], None],
            int,
            signal.Handlers,
            None,
        ],
        this_frame: Optional[FrameType],
    ) -> None:
        # Capture all states to a storage.
        Watchdog.capture_state(depth=1)

        # Set alarm for next signal.
        # TODO: Adaptive sampling.
        # TODO: Compensate for time drift.
        Watchdog._set_alarm(Watchdog.__args.cpu_sampling_rate)

    """Explicit Imports"""

    @staticmethod
    def _strip_argv_if_module() -> bool:
        if len(sys.argv) >= 2 and sys.argv[0] == "-m":
            # Remove -m and the provided module name
            _, mod_name, *sys.argv = sys.argv

            # Given `some.module`, find the path of the corresponding
            # some/module/__main__.py or some/module.py file to run.
            _, spec, _ = Watchdog._get_module_details(mod_name)
            if not spec.origin:
                raise FileNotFoundError

            # Prepend the found .py file to arguments
            sys.argv.insert(0, spec.origin)

            return True
        else:
            return False

    @staticmethod
    def _get_module_details(
        mod_name: str,
        error: Type[Exception] = ImportError,
    ) -> Tuple[str, ModuleSpec, CodeType]:
        """Copy of `runpy._get_module_details`, but not private."""
        if mod_name.startswith("."):
            raise error("Relative module names not supported")
        pkg_name, _, _ = mod_name.rpartition(".")
        if pkg_name:
            # Try importing the parent to avoid catching initialization errors
            try:
                __import__(pkg_name)
            except ImportError as e:
                # If the parent or higher ancestor package is missing, let the
                # error be raised by find_spec() below and then be caught. But do
                # not allow other errors to be caught.
                if e.name is None or (
                    e.name != pkg_name and not pkg_name.startswith(e.name + ".")
                ):
                    raise
            # Warn if the module has already been imported under its normal name
            existing = sys.modules.get(mod_name)
            if existing is not None and not hasattr(existing, "__path__"):
                from warnings import warn

                msg = (
                    "{mod_name!r} found in sys.modules after import of "
                    "package {pkg_name!r}, but prior to execution of "
                    "{mod_name!r}; this may result in unpredictable "
                    "behaviour".format(mod_name=mod_name, pkg_name=pkg_name)
                )
                warn(RuntimeWarning(msg))

        try:
            spec = importlib.util.find_spec(mod_name)
        except (ImportError, AttributeError, TypeError, ValueError) as ex:
            # This hack fixes an impedance mismatch between pkgutil and
            # importlib, where the latter raises other errors for cases where
            # pkgutil previously raised ImportError
            msg = "Error while finding module specification for {!r} ({}: {})"
            if mod_name.endswith(".py"):
                msg += (
                    f". Try using '{mod_name[:-3]}' instead of "
                    f"'{mod_name}' as the module name."
                )
            raise error(msg.format(mod_name, type(ex).__name__, ex)) from ex
        if spec is None:
            raise error("No module named %s" % mod_name)
        if spec.submodule_search_locations is not None:
            if mod_name == "__main__" or mod_name.endswith(".__main__"):
                raise error("Cannot use package as __main__ module")
            try:
                pkg_main_name = mod_name + ".__main__"
                return Watchdog._get_module_details(pkg_main_name, error)
            except error as e:
                if mod_name not in sys.modules:
                    raise  # No module loaded; being a package is irrelevant
                raise error(
                    ("%s; %r is a package and cannot " + "be directly executed")
                    % (e, mod_name)
                )
        loader = spec.loader
        # use isinstance instead of `is None` to placate mypy
        if not isinstance(loader, SourceLoader):
            raise error(
                "%r is a namespace package and cannot be executed" % mod_name
            )
        try:
            code = loader.get_code(mod_name)
        except ImportError as e:
            raise error(format(e)) from e
        if code is None:
            raise error("No code object available for %s" % mod_name)
        return mod_name, spec, code

    @staticmethod
    def _get_executable() -> str:
        # Look for something ending in '.py'.
        progs = [x for x in sys.argv if re.match(r".*\.py$", x)]
        # Just in case that didn't work, try sys.argv[0] and __file__.
        with contextlib.suppress(Exception):
            progs.extend((sys.argv[0], __file__))
        if not progs:
            raise FileNotFoundError

        # Treat the first one as our executable.
        return progs[0]

    def __init__(self, args: WatchdogArguments) -> None:
        assert sys.platform != "win32"
        # Register the exit handler to run when the program terminates or we quit.
        atexit.register(Watchdog._exit_handler)

    """Capture Function"""

    @staticmethod
    def capture_state(depth=0) -> None:
        # EXPERIMENT: Counters and metrics
        start_time = time.perf_counter()
        capture_id = Watchdog.__capture_id
        timestamp = time.time()
        state_size = -1
        state_delta_size = -1
        time_elapsed: float = -1
        Watchdog.__capture_id += 1

        program_state = None
        try:
            # Capture state
            program_state, same_frames = Watchdog.__capture_core.capture_state(
                depth=depth+1,
                truncate_at_frame_id=Watchdog.__exec_capture_frame_id,
            )
            if Watchdog.__args.verbosity >= 2:
                logger.info(f"{program_state}")

            # Find delta
            state_delta = StateDelta.delta(
                Watchdog.__previous_program_state,
                program_state,
                same_frames,
            )
            state_delta_bytes = pickle.dumps(state_delta)
            state_delta_size = len(state_delta_bytes)
            if Watchdog.__args.verbosity >= 2:
                logger.info(f"{state_delta}")
            logger.info(f"Found delta having {state_delta_size} bytes")

            # Persist delta
            if Watchdog.__args.capture_delta_file is not None:
                with open(Watchdog.__args.capture_delta_file, "wb") as fdelta:
                    fdelta.write(state_delta_bytes)
                    fdelta.flush()
                    os.fsync(fdelta)
                logger.info(f"Persisted delta at {Watchdog.__args.capture_delta_file}")

            # Step forward
            Watchdog.__previous_program_state = program_state
        except TypeNotSupportedError as e:
            logger.error(f"Failed to capture frames. {e}")
            pass
        except (TypeError, NotImplementedError, pickle.PicklingError) as e:
            logger.error(f"Failed to pickle state. {e}")
            pass
        except AttributeError as e:
            logger.exception(f"Faulty pickle serialization. {e}")
            pass
        except KeyboardInterrupt:
            logger.info("Watchdog execution interrupted during _cpu_signal_handler.")
            raise
        finally:
            del program_state

        # EXPERIMENT: Final counters and record
        end_time = time.perf_counter()
        time_elapsed = end_time - start_time
        if Watchdog.__args.capture_metrics_file is not None:
            Watchdog.__capture_metrics.record(
                capture_id=capture_id,
                timestamp=timestamp,
                state_size=state_size,
                state_delta_size=state_delta_size,
                time_elapsed=time_elapsed,
            )
        logger.info(f'Captured in {time_elapsed:.6f} seconds')

    """Execution"""

    def exec_capture(
        self,
        code: str,
        the_globals: Dict[str, str],
        the_locals: Dict[str, str],
    ) -> Union[str, int, None]:
        # Run the code being profiled.
        Watchdog.__exec_capture_frame_id = id(sys._getframe())
        exit_status: Union[str, int, None] = 0
        self.start()
        try:
            exec(code, the_globals, the_locals)
        except SystemExit as se:
            # Intercept sys.exit and propagate the error code.
            exit_status = se.code
        except KeyboardInterrupt:
            # Cleanly handle keyboard interrupts (quits execution and dumps the profile).
            logger.info("Watchdog execution interrupted.")
        except Exception as e:
            logger.error(f"Error in program being captured:\n {e}")
            traceback.print_exc()
            exit_status = 1
        finally:
            self.stop()
        return exit_status

    """Instrumentation"""

    @staticmethod
    def launch_exec_capture(
        args: WatchdogArguments,
        target_args: List[str],
    ) -> None:
        # Setup signal handler
        assert sys.platform != "win32"
        Watchdog.__orig_signal(
            Watchdog.__signals.interrupt_signal, Watchdog._interruption_handler
        )  # To insert additional step(s) at interruption time (e.g., ctrl-c)

        # Execute target code
        sys.argv = target_args
        with contextlib.suppress(Exception):
            multiprocessing.set_start_method("fork")
        try:
            Watchdog.process_args(args)
            prog = None
            exit_status: Union[str, int, None] = 0
            try:
                module = Watchdog._strip_argv_if_module()
                prog = Watchdog._get_executable()
                logger.info(f"Detected target program \"{prog}\" with arguments \"{target_args}\"")

                with open(prog, "r") as prog_being_profiled:
                    # Read in the code and compile it.
                    code: Any = ""
                    try:
                        code_str = prog_being_profiled.read()
                        code = compile(code_str, prog, "exec")
                    except SyntaxError:
                        traceback.print_exc()
                        sys.exit(1)

                    # Push the program's path.
                    program_path = os.path.dirname(os.path.abspath(prog))
                    if not module:
                        sys.path.insert(0, program_path)

                    # If a program path was specified at the command-line, use it.
                    Watchdog.__program_path = os.getcwd()
                    Watchdog.__program_being_profiled = prog
                    # Grab local and global variables.
                    import __main__
                    the_locals: Dict[str, Any] = {}
                    the_globals = the_locals
                    # Splice in the name of the file being executed instead of the profiler.
                    the_globals["__file__"] = os.path.abspath(prog)
                    # Some mysterious module foo to make this work the same with -m as with `Watchdog`.
                    the_globals["__spec__"] = None
                    # Insert same builtins.
                    the_globals["__builtins__"] = __main__.__dict__["__builtins__"]
                    # Set target program as main.
                    the_globals["__name__"] = "__main__"
                    # Do a GC before we start.
                    gc.collect()
                    # Start the profiler.
                    profiler = Watchdog(args)
                    try:
                        # We exit with this status (returning error code as appropriate).
                        exit_status = profiler.exec_capture(code, the_locals, the_globals)
                        sys.exit(exit_status)
                    except AttributeError:
                        # don't let the handler below mask programming errors
                        raise
                    except Exception as ex:
                        logger.error(
                            f"Watchdog: An exception of type {type(ex).__name__} occurred. "
                            f"Arguments:\n{ex.args}"
                        )
                        logger.error(traceback.format_exc())
            except (FileNotFoundError, IOError):
                if prog:
                    logger.error(f"Watchdog: could not find input file {prog}")
                else:
                    logger.error("Watchdog: no input file specified.")
                sys.exit(1)
        except SystemExit:
            pass
        except Exception:
            logger.error(f"Watchdog failed to initialize.\n{traceback.format_exc()}")
            sys.exit(1)
        finally:
            if args.capture_metrics_file is not None:
                Watchdog.__capture_metrics.save_to(args.capture_metrics_file)
                logger.info(f"Save capture metrics to {args.capture_metrics_file}")
            sys.exit(exit_status)

    @staticmethod
    def main(args: List[str]) -> None:
        watchdog_args, target_args = Watchdog.parse_args(args)
        logger.info(f"Args: {watchdog_args}")
        if watchdog_args.logger_file is not None:
            logger.add(watchdog_args.logger_file)
        Watchdog.launch_exec_capture(watchdog_args, target_args)


if __name__ == "__main__":
    Watchdog.main(sys.argv)
