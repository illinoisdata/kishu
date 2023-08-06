"""Classes that define a state."""
from __future__ import annotations

import dill as pickle
import types
from io import BytesIO
from types import CodeType, FrameType
from typing import Any, Dict, List

from kishu.exceptions import TypeNotSupportedError


"""
Control flags/constants
"""
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL
PRINT_CELL_SIZE = False


"""
Convenience types
"""
Cells = Dict[str, Any]  # Mapping from variable names to their objects.
SerializedCells = Dict[str, bytes]  # Mapping from variable names to their serialized objects.


class ContinuousPickler:
    """
    Pickler that memorizes shared reference across multiple dumps.

        pickler = ContinuousPickler()
        pickler.dumps(obj_1)
        pickler.dumps(obj_2)
        ...
    """

    def __init__(self):
        """Constructor."""
        self.bytes_io = BytesIO()
        self.pickler = pickle.Pickler(
            file=self.bytes_io,
            protocol=PICKLE_PROTOCOL,
        )

    def dumps(self, obj):
        """Serialize object possibly with previous shared reference."""
        self.pickler.dump(obj)
        pickled_value = self.bytes_io.getvalue()

        # Reset the buffer
        self.bytes_io.seek(0)
        self.bytes_io.truncate()

        return pickled_value


"""
The following are classes defining a state in order from lowest to highest level.
  1. Frame = Scope + Code + Execution
  2. State = List[Frame]
"""


class Scope:
    """A scope is a set of visible variables."""

    def __init__(self, cells: Cells) -> None:
        """Constructor."""
        self.cells: Cells = cells

    @staticmethod
    def parse_from(raw_scope: Dict[str, Any]) -> Scope:
        """
        Parse Python's scope dictionary into serializable object.
        """
        cells: Dict[str, Any] = {}
        for var_name, var_value in raw_scope.items():
            # Here we list all primitive types to be enabled as we develop.
            if isinstance(var_value, types.FunctionType):
                cells[var_name] = var_value
            elif isinstance(var_value, types.LambdaType):
                raise TypeNotSupportedError('LambdaType', var_name, var_value)
            elif isinstance(var_value, types.GeneratorType):
                raise TypeNotSupportedError('GeneratorType', var_name, var_value)
            elif isinstance(var_value, types.CoroutineType):
                raise TypeNotSupportedError('CoroutineType', var_name, var_value)
            elif isinstance(var_value, types.AsyncGeneratorType):
                raise TypeNotSupportedError('AsyncGeneratorType', var_name, var_value)
            elif isinstance(var_value, types.CodeType):
                cells[var_name] = var_value
            elif isinstance(var_value, types.MethodType):
                cells[var_name] = var_value
            elif isinstance(var_value, types.BuiltinFunctionType):
                cells[var_name] = var_value
            elif isinstance(var_value, types.BuiltinMethodType):
                raise TypeNotSupportedError('BuiltinMethodType', var_name, var_value)
            elif isinstance(var_value, types.WrapperDescriptorType):
                raise TypeNotSupportedError('WrapperDescriptorType', var_name, var_value)
            elif isinstance(var_value, types.MethodWrapperType):
                raise TypeNotSupportedError('MethodWrapperType', var_name, var_value)
            elif isinstance(var_value, types.MethodDescriptorType):
                raise TypeNotSupportedError('MethodDescriptorType', var_name, var_value)
            elif isinstance(var_value, types.ClassMethodDescriptorType):
                raise TypeNotSupportedError('ClassMethodDescriptorType', var_name, var_value)
            elif isinstance(var_value, types.ModuleType):
                cells[var_name] = var_value
            elif isinstance(var_value, types.TracebackType):
                raise TypeNotSupportedError('TracebackType', var_name, var_value)
            elif isinstance(var_value, types.FrameType):
                raise TypeNotSupportedError('FrameType', var_name, var_value)
            elif isinstance(var_value, types.GetSetDescriptorType):
                raise TypeNotSupportedError('GetSetDescriptorType', var_name, var_value)
            elif isinstance(var_value, types.MemberDescriptorType):
                raise TypeNotSupportedError('MemberDescriptorType', var_name, var_value)
            elif isinstance(var_value, types.MappingProxyType):
                raise TypeNotSupportedError('MappingProxyType', var_name, var_value)
            else:
                cells[var_name] = var_value

        return Scope(cells=cells)

    def _get(self, name: str) -> Any:
        if name in self.cells:
            return self.cells[name]
        else:
            raise NameError(f"{name} not exist in scope.")

    def _get_cells(self) -> Cells:
        return self.cells

    def _update(self, target_locals: Cells) -> None:
        for key, value in self.cells.items():
            target_locals.setdefault(key, value)

    def __repr__(self) -> str:
        if PRINT_CELL_SIZE:
            cells = {
                k: len(pickle.dumps(v, protocol=PICKLE_PROTOCOL))
                for k, v in self.cells.items()
            }
        else:
            cells = self.cells
        return f'Scope({cells})'


class Code:
    def __init__(
        self,
        argcount,
        cellvars,
        consts,
        filename,
        firstlineno,
        flags,
        lnotab,
        freevars,
        kwonlyargcount,
        name,
        names,
        nlocals,
        stacksize,
        varnames,
    ) -> None:
        """Constructor."""
        self.argcount = argcount
        self.cellvars = cellvars
        self.consts = consts
        self.filename = filename
        self.firstlineno = firstlineno
        self.flags = flags
        self.lnotab = lnotab
        self.freevars = freevars
        self.kwonlyargcount = kwonlyargcount
        self.name = name
        self.names = names
        self.nlocals = nlocals
        self.stacksize = stacksize
        self.varnames = varnames

    @staticmethod
    def parse_from(raw_code: CodeType) -> Code:
        """
        Parse Python's code into serializable object.
        Refer to https://docs.python.org/3/library/inspect.html for code object.
        """
        argcount = raw_code.co_argcount
        # code = raw_code.co_code
        cellvars = raw_code.co_cellvars
        consts = raw_code.co_consts
        filename = raw_code.co_filename
        firstlineno = raw_code.co_firstlineno
        flags = raw_code.co_flags
        lnotab = raw_code.co_lnotab
        freevars = raw_code.co_freevars
        # posonlyargcount = raw_code.co_posonlyargcount
        kwonlyargcount = raw_code.co_kwonlyargcount
        name = raw_code.co_name
        # qualname = raw_code.co_qualname
        names = raw_code.co_names
        nlocals = raw_code.co_nlocals
        stacksize = raw_code.co_stacksize
        varnames = raw_code.co_varnames
        return Code(
            argcount=argcount,
            cellvars=cellvars,
            consts=consts,
            filename=filename,
            firstlineno=firstlineno,
            flags=flags,
            lnotab=lnotab,
            freevars=freevars,
            kwonlyargcount=kwonlyargcount,
            name=name,
            names=names,
            nlocals=nlocals,
            stacksize=stacksize,
            varnames=varnames,
        )

    def __repr__(self):
        return 'Code(' \
            f'argcount= {self.argcount}, ' \
            f'cellvars= {self.cellvars}, ' \
            f'consts= {self.consts}, ' \
            f'filename= {self.filename}, ' \
            f'firstlineno= {self.firstlineno}, ' \
            f'flags= {self.flags}, ' \
            f'lnotab= {self.lnotab}, ' \
            f'freevars= {self.freevars}, ' \
            f'kwonlyargcount= {self.kwonlyargcount}, ' \
            f'name= {self.name}, ' \
            f'names= {self.names}, ' \
            f'nlocals= {self.nlocals}, ' \
            f'stacksize= {self.stacksize}, ' \
            f'varnames= {self.varnames}' \
            ')'


class Execution:
    def __init__(self, lasti, lineno) -> None:
        self.lasti = lasti
        self.lineno = lineno

    def __repr__(self) -> str:
        return 'Execution(' \
            f'lasti= {self.lasti}, ' \
            f'lineno= {self.lineno}' \
            f')'


class Frame:
    """
    A Frame describes the state of a subroutine. It is extracted from Python frame object to be
    serializable and stable within kishu.

    Frame is decomposed into Scope, Code, and Execution objects.
    """

    def __init__(self, code: Code, execution: Execution, this_locals: Scope) -> None:
        """Constructor."""
        self.code = code
        self.execution = execution
        self.locals = this_locals

    @staticmethod
    def parse_from(raw_frame: FrameType) -> Frame:
        """
        Parse Python's frame into serializable object.
        Refer to https://docs.python.org/3/library/inspect.html for frame object.
        """
        # back = raw_frame.f_back
        # builtins = raw_frame.f_builtins
        code = Code.parse_from(raw_frame.f_code)
        # globals = Scope(raw_frame.f_globals)
        execution = Execution(raw_frame.f_lasti, raw_frame.f_lineno)
        this_locals = Scope.parse_from(raw_frame.f_locals)
        return Frame(
            code=code,
            execution=execution,
            this_locals=this_locals,
        )

    def get(self, name: str) -> Any:
        """
        Get value of a variable inside the frame's scope
        """
        return self.locals._get(name)

    def get_cells(self) -> Cells:
        return self.locals._get_cells()

    def get_execution(self) -> Execution:
        return self.execution

    def __getstate__(self) -> Dict[str, Any]:
        """
        Pickle serialization
        """
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Pickle deserialization
        """
        self.__dict__.update(state)

    def __repr__(self) -> str:
        return 'Frame(' \
            f'execution= {self.execution}' \
            f')' \
            f'\n\twith local {self.locals}' \
            f'\n\twith {self.code}'


class State:
    """
    State represents all information sufficient for a recovery.

    Currently, it is only the callstack---a list of frame objects that contain variable scopes,
    source codes, and execution states.
    """

    def __init__(self, frames: List[Frame]) -> None:
        """Constructor."""
        self.frames = frames

    @staticmethod
    def parse_from(raw_frames: List[FrameType]) -> State:
        frames = [Frame.parse_from(raw_frame) for raw_frame in raw_frames]
        return State(frames=frames)

    def get_frames(self) -> List[Frame]:
        return self.frames

    def summary(self) -> str:
        lines = []
        for frame in self.frames:
            code = frame.code
            locals_str = str(frame.locals)
            exe = frame.execution
            line = f'{hex(id(frame))}  {code.filename}::{code.name} @ {exe.lasti}, {locals_str}'
            lines.append(line)
        return '\n'.join(lines)

    def __repr__(self) -> str:
        frames_str = '\n'.join([frame.__repr__() for frame in self.frames])
        frames_str = frames_str.replace('\n', '\n\t')
        return f'State(\n\t{frames_str}\n)'
