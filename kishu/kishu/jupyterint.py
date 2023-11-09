"""
Kishu-Jupyter Integration Module (2nd version)

# Basic Usage

```
from kishu import load_kishu
load_kishu()
```
Then, all the cell executions are recorded, and the result of each cell execution is checkpointed.


# Working with Kishu

load_kishu() adds a new variable `_kishu` (of type KishuJupyterExecHistory) to Jupyter's namespace.
The special variable can be used for kishu-related operations, as follows:
1. browse the history: _kishu.log()
2. see the database file: _kishu.checkpoint_file()
3. restore a state: _kishu.checkout(commit_id)

*Note:* currently, "restore" is limited to restoring a variable state, not including code state.

# New checkpoint file for each Python kernel process.

A new database file is created for each load_kishu(). In the same session, invoking load_kishu()
multiple times returns the same singleton instance. In a new session, the function will return
a different instance (associated with a different checkpoint file).

Restoring a checkpointed state means that we are restoring some of the variables from an old state
into the current state. Thus, the kishu object remains the same before and after any checkpointing/
restoration operations; only the current state (or the variables inside it) changes.

(Not implemented yet)
In order to give an impression that we are actually reviving an old state, kishu also manages
IPython's database including execution count and cell code.


Reference
- https://ipython.readthedocs.io/en/stable/config/callbacks.html
"""
from __future__ import annotations

import dill as pickle
import enum
import IPython
import ipylab
import json
import jupyter_client
import nbformat
import os
import time
import uuid

from dataclasses import dataclass
from datetime import datetime
from jupyter_ui_poll import run_ui_poll_loop
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from kishu.exceptions import (
    JupyterConnectionError,
    KernelNotAliveError,
    MissingConnectionInfoError,
    MissingNotebookMetadataError,
    NoChannelError,
    StartChannelError,
)
from kishu.notebook_id import NotebookId
from kishu.planning.namespace import Namespace
from kishu.planning.plan import ExecutionHistory, RestorePlan, StoreEverythingCheckpointPlan, UnitExecution
from kishu.planning.planner import CheckpointRestorePlanner
from kishu.runtime import JupyterRuntimeEnv
from kishu.storage.branch import KishuBranch
from kishu.storage.checkpoint_io import init_checkpoint_database
from kishu.storage.commit_graph import KishuCommitGraph
from kishu.storage.path import KishuPath


"""
Functions to find enclosing notebook name, distilled From ipynbname.
"""


def enclosing_platform() -> str:
    app = ipylab.JupyterFrontEnd()
    num_trials = 10

    def app_commands_fn():
        nonlocal num_trials
        if app.commands.list_commands() == [] and num_trials > 0:
            num_trials -= 1
            return None
        return app.commands.list_commands()

    # To fetch the command list, we need to unblock the frontend through polling loop.
    try:
        app_commands = run_ui_poll_loop(app_commands_fn)
        if "docmanager:save" in app_commands:
            # In JupyterLab.
            return "jupyterlab"
    except Exception:
        # BUG: run_ui_poll_loop throws when not in a ipython kernel.
        pass

    # In Jupyter Notebook.
    return "jupyternb"


class BareReprStr(str):

    def __init__(self, s: str):
        self.s = s

    def __repr__(self):
        return self.s


"""
Notebook instrument.
"""


@dataclass
class KishuSession:
    notebook_key: str
    kernel_id: Optional[str]
    notebook_path: Optional[str]
    is_alive: bool


class CommitEntryKind(str, enum.Enum):
    unspecified = "unspecified"
    jupyter = "jupyter"
    manual = "manual"


@dataclass
class FormattedCell:
    cell_type: str
    source: str
    output: Optional[str]
    execution_count: Optional[int]


@dataclass
class CommitEntry(UnitExecution):
    """
    Records the information related to Jupyter's cell execution.

    @param execution_count  The ipython-tracked execution count, which is used for displaying
                            the cell number on Jupyter.
    @param result  A printable form of the returned result (obtained by __repr__).
    @param start_time_ms  The epoch time in milliseconds. Obtained by round(time.time()*1000).
            start_time_ms=None means that the start time is unknown, which is the case when
            the callback is first registered.
    @param end_time_ms  The epoch time the cell execution completed.
    @param runtime_ms  The difference betweeen start_time_ms and end_time_ms.
    @param checkpoint_runtime_ms  The overhead of checkpoint operation (after the execution of
            the cell).
    @param checkpoint_vars  The variable names that are checkpointed after the cell execution.
    @param restore_plan  The checkpoint algorithm also sets this restoration plan, which
            when executed, restores all the variables as they are.
    """
    kind: CommitEntryKind = CommitEntryKind.unspecified

    checkpoint_runtime_ms: Optional[int] = None
    checkpoint_vars: Optional[List[str]] = None
    executed_cells: Optional[List[str]] = None
    raw_nb: Optional[str] = None
    formatted_cells: Optional[List[FormattedCell]] = None
    restore_plan: Optional[RestorePlan] = None
    message: str = ""
    timestamp_ms: int = 0
    ahg_string: Optional[str] = None
    code_version: int = 0
    var_version: int = 0

    # Only available in jupyter commit entries
    execution_count: Optional[int] = None
    error_before_exec: Optional[str] = None
    error_in_exec: Optional[str] = None
    result: Optional[str] = None
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None


@dataclass
class JupyterCommandResult:
    status: str
    message: str


class JupyterConnection:
    def __init__(self, kernel_id: str) -> None:
        self.kernel_id = kernel_id
        self.km: Optional[jupyter_client.BlockingKernelClient] = None

    @staticmethod
    def from_notebook_key(notebook_key: str) -> JupyterConnection:
        # Find connection information
        conn_info = NotebookId.try_retrieve_connection(notebook_key)
        if conn_info is None:
            raise MissingConnectionInfoError()
        return JupyterConnection(conn_info.kernel_id)

    def __enter__(self) -> JupyterConnection:
        # Find connection file.
        try:
            cf = jupyter_client.find_connection_file(self.kernel_id)
        except OSError:
            raise KernelNotAliveError()

        # Connect to kernel.
        self.km = jupyter_client.BlockingKernelClient(connection_file=cf)
        self.km.load_connection_file()
        self.km.start_channels()
        self.km.wait_for_ready()
        if not self.km.is_alive():
            self.km = None
            raise StartChannelError()

        return self

    def execute(self, command: str, pre_command: str = "") -> Dict[str, Any]:
        if self.km is None:
            raise NoChannelError()
        return self.km.execute_interactive(
            pre_command,  # Not capture output.
            user_expressions={"command_result": command},  # To get output from command.
            silent=True,  # Do not increment cell count and trigger pre/post_run_cell hooks.
        )

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.km is not None:
            self.km.stop_channels()
            self.km = None

    def execute_one_command(self, command: str, pre_command: str = "") -> JupyterCommandResult:
        try:
            with self as conn:
                reply = conn.execute(command, pre_command=pre_command)
        except JupyterConnectionError as e:
            return JupyterCommandResult(
                status="error",
                message=str(e),
            )

        # Handle unexpected status.
        if reply["content"]["status"] == "error":
            # print("\n".join(reply["content"]["traceback"]))
            ename = reply["content"]["ename"]
            evalue = reply["content"]["evalue"]
            return JupyterCommandResult(
                status="error",
                message=f"{ename}: {evalue}",
            )
        elif reply["content"]["status"] != "ok":
            return JupyterCommandResult(
                status=reply["content"]["status"],
                message=json.dumps(reply["content"]),
            )

        # Reply status is ok.
        command_result = reply["content"].get("user_expressions", {}).get("command_result", {})
        command_result_status = command_result.get("status", "")
        if command_result_status == 'error':
            ename = command_result["ename"]
            evalue = command_result["evalue"]
            return JupyterCommandResult(
                status="error",
                message=f"{ename}: {evalue}",
            )
        elif command_result_status == 'ok':
            command_result_data = command_result.get("data", {}).get("text/plain", "")
            return JupyterCommandResult(
                status="ok",
                message=command_result_data,
            )
        else:
            return JupyterCommandResult(
                status="ok",
                message=f"Executed {command} but no result.",
            )


class KishuForJupyter:
    CURRENT_CELL_ID = 'current'
    SAVE_CMD = "try { IPython.notebook.save_checkpoint(); } catch { }"

    def __init__(self, notebook_id: NotebookId) -> None:
        """
        @param _history  The connector to log data.
        @param _running_cell  A temporary data created during a cell execution.
        @param _checkpoint_file  The file for storing all the data.
        """
        self._notebook_id = notebook_id
        self._commit_id_mode = "uuid4"  # TODO: Load from environment/configuration
        self._enable_auto_branch = True
        self._enable_auto_commit_when_skip_notebook = True
        init_checkpoint_database(self.checkpoint_file())
        self._history: ExecutionHistory = ExecutionHistory(self.checkpoint_file())
        self._graph: KishuCommitGraph = KishuCommitGraph.new_on_file(
            KishuPath.commit_graph_directory(self._notebook_id.key())
        )
        try:
            self._notebook_id.record_connection()
        except Exception as e:
            print(f"WARNING: Skipped retrieving connection info due to {repr(e)}.")

        self._platform = enclosing_platform()
        self._session_id = 0
        self._last_execution_count = 0
        self._start_time_ms: Optional[int] = None
        self._test_mode = False

        self._cr_planner = CheckpointRestorePlanner.from_existing(
            Namespace({}) if kishu_ipython() is None
            else Namespace(kishu_ipython().user_ns),
            kishu_ipython_in()
        )

    def set_test_mode(self):
        # Configure this object for testing.
        self._test_mode = True
        self._commit_id_mode = "counter"

    def set_session_id(self, session_id):
        self._session_id = session_id

    def __str__(self):
        return (
            "KishuForJupyter("
            f"id: {self._notebook_id.key()}, "
            f"path: {self._notebook_id.path()})"
        )

    def __repr__(self):
        return (
            "KishuForJupyter("
            f"notebook_id: {self._notebook_id.key()}, "
            f"kernel_id: {self._notebook_id.kernel_id()}, "
            f"notebook_path: {self._notebook_id.path()}, "
            f"session_id: {self._session_id}, "
            f"platform: {self._platform}, "
            f"commit_id_mode: {self._commit_id_mode})"
        )

    def log(self) -> ExecutionHistory:
        return self._history

    def checkpoint_file(self) -> str:
        return KishuPath.checkpoint_path(self._notebook_id.key())

    def get_user_namespace_vars(self) -> Set[str]:
        ip = kishu_ipython()
        user_ns = {} if ip is None else ip.user_ns
        return set(varname for varname, _ in filter(no_ipython_var, user_ns.items()))

    def checkout(self, branch_or_commit_id: str, skip_notebook: bool = False) -> BareReprStr:
        """
        Restores a variable state from commit_id.
        """
        ip = kishu_ipython()
        if ip is None:
            raise ValueError("Jupyter kernel is unexpectedly None.")

        # By default, checkout at commit ID in detach mode.
        branch_name: Optional[str] = None
        commit_id = branch_or_commit_id
        is_detach = True

        # Attempt to interpret target as a branch.
        retrieved_branches = KishuBranch.get_branch(self._notebook_id.key(), branch_or_commit_id)
        if len(retrieved_branches) == 1:
            assert retrieved_branches[0].branch_name == branch_or_commit_id
            branch_name = retrieved_branches[0].branch_name
            commit_id = retrieved_branches[0].commit_id
            is_detach = False

        # Retrieve checkout plan.
        checkpoint_file = self.checkpoint_file()
        commit_id = KishuForJupyter.disambiguate_commit(self._notebook_id.key(), commit_id)
        unit_exec_cell = UnitExecution.get_from_db(checkpoint_file, commit_id)
        commit_entry = cast(CommitEntry, unit_exec_cell)
        if commit_entry.restore_plan is None:
            raise ValueError("No restore plan found for commit_id = {}".format(commit_id))

        # Restore notebook cells.
        if not skip_notebook and commit_entry.raw_nb is not None:
            self._checkout_notebook(commit_entry.raw_nb)

        # Restore list of executed cells.
        if commit_entry.executed_cells is not None:
            current_executed_cells = kishu_ipython_in()
            if current_executed_cells is not None:
                current_executed_cells[:] = commit_entry.executed_cells[:]

        # Restore user-namespace variables.
        user_ns = ip.user_ns   # will restore to global namespace
        target_ns: Dict[str, Any] = {}         # temp location
        commit_entry.restore_plan.run(target_ns, checkpoint_file, commit_id)
        self._checkout_namespace(user_ns, target_ns)

        # Update C/R planner with AHG from checkpoint file and new namespace.
        if commit_entry.ahg_string is None:
            raise ValueError("No Application History Graph found for commit_id = {}".format(commit_id))
        self._cr_planner.replace_state(commit_entry.ahg_string, user_ns)

        # Update Kishu heads.
        self._graph.jump(commit_id)
        KishuBranch.update_head(
            self._notebook_id.key(),
            branch_name=branch_name,
            commit_id=commit_id,
            is_detach=is_detach,
        )

        # Create new commit when skip restoring notebook.
        if self._enable_auto_commit_when_skip_notebook and skip_notebook:
            new_commit = self.commit(f"Auto-commit after checking out {commit_id} only variables.")
            return BareReprStr(f"Checkout {commit_id} only variables and commit {new_commit}.")

        if is_detach:
            return BareReprStr(f"Checkout {commit_id} in detach mode.")
        return BareReprStr(f"Checkout {branch_or_commit_id} ({commit_id}).")

    def pre_run_cell(self, info) -> None:
        """
        A hook invoked before running a cell.

        Example:
        print('info.raw_cell =', info.raw_cell)
        print('info.store_history =', info.store_history)
        print('info.silent =', info.silent)
        print('info.shell_futures =', info.shell_futures)
        print('info.cell_id =', info.cell_id)
        print(dir(info))
        """
        self._start_time_ms = get_epoch_time_ms()

        self._cr_planner.pre_run_cell_update(self.get_user_namespace_vars())

    def post_run_cell(self, result) -> None:
        """
        A hook executed after the execution of each cell.

        Example:
        print('result.execution_count = ', result.execution_count)
        print('result.error_before_exec = ', result.error_before_exec)
        print('result.error_in_exec = ', result.error_in_exec)
        print('result.info = ', result.info)
        print('result.result = ', result.result)
        """
        entry = CommitEntry(kind=CommitEntryKind.jupyter)
        entry.execution_count = result.execution_count
        short_raw_cell = result.info.raw_cell if len(result.info.raw_cell) <= 20 else f"{result.info.raw_cell[:20]}..."
        entry.message = f"Auto-commit after executing < {short_raw_cell} >"

        # Jupyter-specific info for commit entry.
        entry.start_time_ms = self._start_time_ms
        entry.end_time_ms = get_epoch_time_ms()
        if entry.start_time_ms is not None:
            entry.runtime_ms = entry.end_time_ms - entry.start_time_ms
        entry.code_block = result.info.raw_cell
        entry.error_before_exec = repr_if_not_none(result.error_before_exec)
        entry.error_in_exec = repr_if_not_none(result.error_in_exec)
        entry.result = repr_if_not_none(result.result)

        # Update optimization items.
        self._cr_planner.post_run_cell_update(
            entry.code_block,
            self.get_user_namespace_vars(),
            entry.start_time_ms,
            entry.runtime_ms,
        )

        # Step forward internal data.
        self._last_execution_count = result.execution_count
        self._start_time_ms = None

        self._commit_entry(entry)

    @staticmethod
    def kishu_sessions() -> List[KishuSession]:
        # List alive IPython sessions.
        alive_kernels = {session.kernel_id: session for session in JupyterRuntimeEnv.iter_sessions()}

        # List all Kishu sessions.
        sessions = []
        for notebook_key in KishuPath.iter_notebook_keys():
            cf = NotebookId.try_retrieve_connection(notebook_key)

            # Connection file not found.
            if cf is None:
                sessions.append(KishuSession(
                    notebook_key=notebook_key,
                    kernel_id=None,
                    notebook_path=None,
                    is_alive=False,
                ))
                continue

            # No matching alive kernel ID.
            if cf.kernel_id not in alive_kernels:
                sessions.append(KishuSession(
                    notebook_key=notebook_key,
                    kernel_id=cf.kernel_id,
                    notebook_path=cf.notebook_path,
                    is_alive=False,
                ))
                continue

            # No matching notebook with notebook key in its metadata.
            notebook_path = alive_kernels[cf.kernel_id].notebook_path
            written_notebook_key: Optional[str] = None
            try:
                written_notebook_key = NotebookId.parse_key_from_path(notebook_path)
            except (FileNotFoundError, MissingNotebookMetadataError):
                pass
            if notebook_key != written_notebook_key:
                sessions.append(KishuSession(
                    notebook_key=notebook_key,
                    kernel_id=cf.kernel_id,
                    notebook_path=cf.notebook_path,
                    is_alive=False,
                ))
                continue

            # Kernel ID is alive. Replace notebook path with the newest one.
            sessions.append(KishuSession(
                notebook_key=notebook_key,
                kernel_id=cf.kernel_id,
                notebook_path=str(notebook_path),
                is_alive=True,
            ))
        return sessions

    @staticmethod
    def disambiguate_commit(notebook_key: str, commit_id: str) -> str:
        checkpoint_file = KishuPath.checkpoint_path(notebook_key)
        possible_commit_ids = UnitExecution.keys_from_db_like(checkpoint_file, commit_id)
        if len(possible_commit_ids) == 0:
            raise ValueError(f"No commit with ID {repr(commit_id)}")
        if commit_id in possible_commit_ids:
            return commit_id
        if len(possible_commit_ids) > 1:
            raise ValueError(f"Ambiguous commit ID {repr(commit_id)}, having many choices {possible_commit_ids}.")
        return possible_commit_ids[0]

    def commit(self, message: Optional[str] = None) -> BareReprStr:
        entry = CommitEntry(kind=CommitEntryKind.manual)
        entry.execution_count = self._last_execution_count
        entry.message = message if message is not None else f"Manual commit after {entry.execution_count} executions."
        self._commit_entry(entry)
        return BareReprStr(entry.exec_id)

    def _commit_entry(self, entry: CommitEntry) -> None:
        # Generate commit ID.
        entry.exec_id = self._commit_id()
        entry.timestamp_ms = get_epoch_time_ms()

        # Force saving to observe all cells and extract notebook informations.
        self._save_notebook()
        entry.executed_cells = kishu_ipython_in()
        entry.raw_nb, entry.formatted_cells = self._all_notebook_cells()
        if entry.formatted_cells is not None:
            code_cells = []
            for cell in entry.formatted_cells:
                code_cells.append(cell.cell_type)
                code_cells.append(cell.source)
            entry.code_version = hash(tuple(code_cells))

        # Plan for checkpointing and restoration.
        checkpoint_start_sec = time.time()
        entry.restore_plan, entry.var_version = self._checkpoint(entry)
        entry.ahg_string = self._cr_planner.serialize_ahg()
        checkpoint_runtime_ms = round((time.time() - checkpoint_start_sec) * 1000)
        entry.checkpoint_runtime_ms = checkpoint_runtime_ms

        # Update other structures.
        self._history.append(entry)
        self._graph.step(entry.exec_id)
        self._step_branch(entry.exec_id)

    def _commit_id(self) -> str:
        if self._commit_id_mode == "counter":
            return str(self._session_id) + ":" + str(self._last_execution_count)
        return str(uuid.uuid4())

    def _checkpoint(self, cell_info: CommitEntry) -> Tuple[RestorePlan, int]:
        """
        Performs checkpointing and creates a matching restoration plan.

        TODO: Perform more intelligent checkpointing.
        """
        # Step 1: checkpoint
        ip = kishu_ipython()
        user_ns = {} if ip is None else ip.user_ns
        checkpoint_file = self.checkpoint_file()
        exec_id = cell_info.exec_id
        filter_user_ns = {item[0]: item[1] for item in user_ns.items() if no_ipython_var(item)}
        cell_info.checkpoint_vars = list(filter_user_ns.keys())
        checkpoint = StoreEverythingCheckpointPlan.create(
            user_ns,
            checkpoint_file,
            exec_id,
            cell_info.checkpoint_vars,
        )
        checkpoint.run(user_ns)

        # Step 2: prepare a restoration plan using results from the optimizer.
        restore_plan = self._cr_planner.generate_restore_plan()

        # Extra: generate variable version. TODO: we should avoid the extra namespace serialization.
        var_version = hash(pickle.dumps(filter_user_ns))
        return restore_plan, var_version

    def _save_notebook(self) -> None:
        # TODO re-enable notebook saving during tests when possible/supported
        if self._test_mode:
            return
        nb_path = self._notebook_id.path()

        # Remember starting state.
        start_mtime = os.path.getmtime(nb_path)
        current_mtime = start_mtime

        # Issue save command.
        if self._platform == "jupyterlab":
            # In JupyterLab.
            app = ipylab.JupyterFrontEnd()
            run_ui_poll_loop(lambda: (  # This unblocks web UI to connect with app.
                None if app.commands.list_commands() == []
                else app.commands.list_commands()
            ))
            app.commands.execute("docmanager:save")
        else:
            # In Jupyter Notebook.
            IPython.display.display(IPython.display.Javascript(KishuForJupyter.SAVE_CMD))

        # Now wait for the saving to change the notebook.
        sleep_t = 0.2
        time.sleep(sleep_t)
        while start_mtime == current_mtime and sleep_t < 1.0:
            current_mtime = os.path.getmtime(nb_path)
            sleep_t *= 1.2
            time.sleep(sleep_t)
        if sleep_t >= 1.0:
            print("WARNING: Notebook saving is taking too long. Kishu may not capture every cell.")

    def _all_notebook_cells(self) -> Tuple[Optional[str], List[FormattedCell]]:
        nb = JupyterRuntimeEnv.read_notebook(self._notebook_id.path())
        nb_cells = []
        for cell in nb.cells:
            if cell.cell_type == "code":
                nb_cells.append(FormattedCell(
                    cell_type=cell.cell_type,
                    source=cell.source,
                    output=self._parse_cell_output(cell.outputs),
                    execution_count=cell.execution_count,
                ))
            elif cell.cell_type == "markdown":
                nb_cells.append(FormattedCell(
                    cell_type=cell.cell_type,
                    source=cell.source,
                    output=None,
                    execution_count=None,
                ))
            else:
                raise ValueError(f"Unknown cell type: {cell.cell_type}")
        return nbformat.writes(nb), nb_cells

    def _parse_cell_output(self, cell_outputs: List[Dict[Any, Any]]) -> Optional[str]:
        if len(cell_outputs) == 0:
            return None
        for cell_output in cell_outputs:
            # Filter auto-saving output.
            if (
                cell_output["output_type"] == "display_data" and
                cell_output["data"].get("application/javascript", "") == KishuForJupyter.SAVE_CMD
            ):
                continue

            # Now parse output into text.
            if cell_output["output_type"] == "stream":
                return cell_output["text"]
            elif cell_output["output_type"] == "execute_result":
                if "text/plain" in cell_output["data"]:
                    return cell_output["data"].get("text/plain", "<execute_result>")
                else:
                    raise ValueError(f"Unknown output data structure: {cell_output['data']}")
            elif cell_output["output_type"] == "display_data":
                return cell_output["data"].get("text/plain", "<display_data>")
            elif cell_output["output_type"] == "error":
                return "\n".join([
                    *cell_output["traceback"],
                    f'{cell_output["ename"]}: {cell_output["evalue"]}',
                ])
            else:
                raise ValueError(f"Unknown output type: {cell_output}")
        return None

    def _step_branch(self, commit_id: str) -> None:
        head = KishuBranch.update_head(self._notebook_id.key(), commit_id=commit_id)
        if self._enable_auto_branch and head.branch_name is None:
            new_branch_name = f"auto_{commit_id}"
            KishuBranch.upsert_branch(self._notebook_id.key(), new_branch_name, commit_id)
            KishuBranch.update_head(self._notebook_id.key(), new_branch_name, commit_id)
        elif head.branch_name is not None:
            KishuBranch.upsert_branch(self._notebook_id.key(), head.branch_name, commit_id)

    def _checkout_notebook(self, raw_nb: str) -> None:
        nb_path = self._notebook_id.path()

        # Read current notebook cells.
        nb = JupyterRuntimeEnv.read_notebook(self._notebook_id.path())

        # Apply target cells.
        target_nb = nbformat.reads(raw_nb, JupyterRuntimeEnv.NBFORMAT_VERSION)
        nb.cells = target_nb.cells

        # Save change
        nbformat.write(nb, nb_path)

    def _checkout_namespace(self, user_ns: Dict[Any, Any], target_ns: Dict[Any, Any]) -> None:
        user_ns.update(target_ns)
        for key, _ in list(filter(no_ipython_var, user_ns.items())):
            if key not in target_ns:
                del user_ns[key]


def repr_if_not_none(obj: Any) -> Optional[str]:
    if obj is None:
        return obj
    return repr(obj)


IPYTHON_VARS = set(['In', 'Out', 'get_ipython', 'exit', 'quit', 'open'])
KISHU_INSTRUMENT = '_kishu'
KISHU_VARS = set(['kishu', 'load_kishu', 'init_kishu', KISHU_INSTRUMENT])


def no_ipython_var(name_obj: Tuple[str, Any]) -> bool:
    """
    @param name  The variable name.
    @param value  The associated object.
    @return  True if name is not an IPython-specific variable.
    """
    name, obj = name_obj
    if name.startswith('_'):
        return False
    if name in IPYTHON_VARS:
        return False
    if name in KISHU_VARS:
        return False
    # if isinstance(obj, KishuJupyterExecHistory):
    #     return False
    if getattr(obj, '__module__', '').startswith('IPython'):
        return False
    return True


def get_epoch_time_ms() -> int:
    return round(time.time() * 1000)


# Interestingly, simply calling get_ipython() does not always access the globally accessible
# function; thus, we are taking this approach.
_kishu_ipython = None


def kishu_ipython():
    return _kishu_ipython


def kishu_ipython_in() -> Optional[List[str]]:
    ip = kishu_ipython()
    if ip is None:
        return None
    return ip.user_ns["In"]


def load_kishu(notebook_id: Optional[NotebookId] = None, session_id: Optional[int] = None) -> None:
    global _kishu_ipython
    if _kishu_ipython is not None:
        return
    _kishu_ipython = eval('get_ipython()')
    ip = kishu_ipython()

    if notebook_id is None:
        notebook_key = datetime.now().strftime('%Y%m%dT%H%M%S')
        notebook_id = NotebookId.from_enclosing_with_key(notebook_key)
    kishu = KishuForJupyter(notebook_id)
    if session_id:
        kishu.set_session_id(session_id)

    ip.user_ns[KISHU_INSTRUMENT] = kishu
    ip.events.register('pre_run_cell', kishu.pre_run_cell)
    ip.events.register('post_run_cell', kishu.post_run_cell)


def init_kishu(notebook_path: Optional[str] = None) -> None:
    """
    1. Create notebook key
    2. Find kernel id using enclosing_kernel_id()
    3. KishuForJupyter
    """
    # Create notebook id object storing path and kernel_id
    if notebook_path is None:
        notebook_id = NotebookId.from_enclosing_with_key("")
    else:
        notebook_id = NotebookId.from_enclosing_with_key_and_path("", Path(notebook_path))

    # Open notebook file
    nb = JupyterRuntimeEnv.read_notebook(notebook_id.path())

    # Update notebook metadata.
    NotebookId.write_kishu_metadata(nb)
    nbformat.write(nb, notebook_id.path())

    # Construct Notebook Id.
    new_key = nb.metadata.kishu.notebook_id
    notebook_id = NotebookId(
        key=new_key,
        path=notebook_id.path(),
        kernel_id=notebook_id.kernel_id(),
    )

    # Attach Kishu instrumentation.
    load_kishu(notebook_id, nb.metadata.kishu.session_count)


def remove_event_handlers() -> None:
    """
    Removes event handlers added by load_kishu
    """
    # access ipython
    ip = kishu_ipython()
    if ip is None:
        return

    if KISHU_INSTRUMENT in ip.user_ns:
        # if kishu is in the user_ns of ipython, delete hooks
        kishu = ip.user_ns[KISHU_INSTRUMENT]
        try:
            ip.events.unregister('pre_run_cell', kishu.pre_run_cell)
        except ValueError:
            # if here, then kishu.pre_run_cell is not attached to notebook, so do nothing
            pass

        try:
            ip.events.unregister('post_run_cell', kishu.post_run_cell)
        except ValueError:
            # if here, then kishu.post_run_cell is not attached to notebook, so do nothing
            pass

        # delete kishu instrument from user_ns
        del ip.user_ns[KISHU_INSTRUMENT]

    # Set global kishu value to be None
    global _kishu_ipython
    _kishu_ipython = None


def detach_kishu(notebook_path: Optional[str] = None) -> None:
    # Create notebook id object
    if notebook_path is None:
        notebook_id = NotebookId.from_enclosing_with_key("")
    else:
        notebook_id = NotebookId.from_enclosing_with_key_and_path("", Path(notebook_path))

    # Open notebook file
    nb = JupyterRuntimeEnv.read_notebook(notebook_id.path())

    try:
        # Remove metadata from notebook
        NotebookId.remove_kishu_metadata(nb)
        nbformat.write(nb, notebook_id.path())
    except MissingNotebookMetadataError:
        # This means that kishu metadata is not in the notebook, so do nothing
        pass

    # Remove all hooks
    remove_event_handlers()
