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
import enum
import ipykernel
import ipylab
import IPython
import json
import jupyter_client
import jupyter_core.paths
import nbformat
import os
import time
import urllib.request
import uuid
import numpy as np

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from itertools import chain
from jupyter_ui_poll import run_ui_poll_loop
from pathlib import Path, PurePath
from typing import Any, cast, Dict, Generator, List, Optional, Tuple

from kishu.branch import KishuBranch
from kishu.checkpoint_io import init_checkpoint_database
from kishu.commit_graph import KishuCommitGraph
from kishu.exceptions import (
    JupyterConnectionError,
    MissingConnectionInfoError,
    KernelNotAliveError,
    StartChannelError,
    NoChannelError,
)
from kishu.resources import KishuResource
from kishu import idgraph2 as idgraph
from kishu.optimization.ahg import AHG
from kishu.optimization.optimizer import Optimizer
from kishu.optimization.profiler import profile_variable_size, profile_migration_speed
from kishu.optimization.change import find_input_vars, find_created_and_deleted_vars

from kishu.plan import ExecutionHistory, StoreEverythingCheckpointPlan, UnitExecution, RestorePlan


"""
Functions to find enclosing notebook name, distilled From ipynbname.
"""


def _list_maybe_running_servers() -> Generator[dict, None, None]:
    runtime_dir = Path(jupyter_core.paths.jupyter_runtime_dir())
    if runtime_dir.is_dir():
        config_files = chain(
            runtime_dir.glob("nbserver-*.json"),  # jupyter notebook (or lab 2)
            runtime_dir.glob("jpserver-*.json"),  # jupyterlab 3
        )
        for file_name in sorted(config_files, key=os.path.getmtime, reverse=True):
            try:
                yield json.loads(file_name.read_bytes())
            except json.JSONDecodeError:
                pass


def _get_sessions(srv: dict):
    try:
        url = f"{srv['url']}api/sessions"
        if srv['token']:
            url += f"?token={srv['token']}"
        with urllib.request.urlopen(url, timeout=1.0) as req:
            return json.load(req)
    except Exception:
        return []


def _find_nb_path(kernel_id: str) -> Tuple[dict, PurePath]:
    for srv in _list_maybe_running_servers():
        for sess in _get_sessions(srv):
            if sess["kernel"]["id"] == kernel_id:
                return srv, PurePath(sess["notebook"]["path"])
    raise LookupError("")


def enclosing_notebook_path(kernel_id: str) -> Path:
    srv, path = _find_nb_path(kernel_id)
    if srv is not None and path is not None:
        return Path(srv.get("root_dir") or srv["notebook_dir"]) / path
    raise FileNotFoundError("Failed to identify notebook file path.")


def enclosing_kernel_id() -> str:
    connection_file_path = ipykernel.get_connection_file()
    connection_file = os.path.basename(connection_file_path)
    if '-' not in connection_file:
        # connection_file not in expected format.
        # TODO: Find more stable way to extract kernel ID.
        raise FileNotFoundError("Failed to identify IPython connection file")
    return connection_file.split('-', 1)[1].split('.')[0]


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
    raw_nb: Optional[str] = None
    formatted_cells: Optional[List[FormattedCell]] = None
    restore_plan: Optional[RestorePlan] = None

    # Only available in jupyter commit entries
    execution_count: Optional[int] = None
    message: str = ""
    error_before_exec: Optional[str] = None
    error_in_exec: Optional[str] = None
    result: Optional[str] = None
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None


@dataclass_json
@dataclass
class JupyterConnectionInfo:
    kernel_id: str
    notebook_path: str


@dataclass
class JupyterCommandResult:
    status: str
    message: str


class JupyterConnection:
    def __init__(self, notebook_id: str) -> None:
        self.notebook_id = notebook_id
        self.km: Optional[jupyter_client.BlockingKernelClient] = None

    def __enter__(self) -> JupyterConnection:
        # Find connection information
        conn_info = KishuForJupyter.retrieve_connection(self.notebook_id)
        if conn_info is None:
            raise MissingConnectionInfoError()

        # Find connection file.
        try:
            cf = jupyter_client.find_connection_file(conn_info.kernel_id)
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

    def execute(self, command: str) -> Dict[str, Any]:
        if self.km is None:
            raise NoChannelError()
        return self.km.execute_interactive(
            "",
            user_expressions={"command_result": command},  # To get output from command.
            silent=True,  # Do not increment cell count and trigger pre/post_run_cell hooks.
        )

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.km is not None:
            self.km.stop_channels()
            self.km = None

    @staticmethod
    def execute_one_command(notebook_id: str, command: str) -> JupyterCommandResult:
        try:
            with JupyterConnection(notebook_id) as conn:
                reply = conn.execute(command)
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
        command_result = JupyterConnection.extract_command_result(reply)
        if command_result is not None:
            return JupyterCommandResult(
                status="ok",
                message=command_result,
            )
        else:
            return JupyterCommandResult(
                status="ok",
                message=f"Successfully execute {command}.",
            )

    @staticmethod
    def extract_command_result(reply: Dict[str, Any]) -> None:
        command_result = reply["content"].get("user_expressions", {}).get("command_result", {})
        if command_result.get("status", "") != "ok":
            return None
        return command_result.get("data", {}).get("text/plain", None)


class KishuForJupyter:
    CURRENT_CELL_ID = 'current'
    SAVE_CMD = "try { IPython.notebook.save_checkpoint(); } catch { }"
    NBFORMAT_VERSION = 4

    def __init__(self, notebook_id: Optional[str] = None) -> None:
        """
        @param _history  The connector to log data.
        @param _running_cell  A temporary data created during a cell execution.
        @param _checkpoint_file  The file for storing all the data.
        """
        if notebook_id is None:
            self._notebook_id = datetime.now().strftime('%Y%m%dT%H%M%S')  # TODO: Use notebook name.
        else:
            self._notebook_id = notebook_id
        self._commit_id_mode = "uuid4"  # TODO: Load from environment/configuration
        init_checkpoint_database(self.checkpoint_file())
        self._history: ExecutionHistory = ExecutionHistory(self.checkpoint_file())
        self._graph: KishuCommitGraph = KishuCommitGraph.new_on_file(
            KishuResource.commit_graph_directory(self._notebook_id)
        )

        self._kernel_id = ""
        self._notebook_path: Optional[Path] = None
        try:
            self._kernel_id = enclosing_kernel_id()
            self._notebook_path = enclosing_notebook_path(self._kernel_id)
            self.record_connection()
        except Exception as e:
            print(f"WARNING: Skipped retrieving connection info due to {repr(e)}.")
        if self._notebook_path:
            print("WARNING: Enclosing notebook not found. Skipping notebook cell checkpoint and restoration.")

        self._platform = enclosing_platform()
        self._session_id = 0
        self._last_execution_count = 0
        self._start_time_ms: Optional[int] = None

        # Optimization items. The AHG for tracking per-cell variable accesses and
        # modifications is initialized here.
        self._ahg = AHG()
        self._user_ns = {} if get_jupyter_kernel() is None else get_jupyter_kernel().user_ns
        self._id_graph_map = {}
        self._pre_run_cell_vars = set()

    def set_test_mode(self):
        # Configure this object for testing.
        self._commit_id_mode = "counter"

    def set_session_id(self, session_id):
        self._session_id = session_id

    def log(self) -> ExecutionHistory:
        return self._history

    def checkpoint_file(self) -> str:
        return KishuResource.checkpoint_path(self._notebook_id)

    def get_user_namespace_vars(self) -> list:
        return [item[0] for item in filter(no_ipython_var, self._user_ns.items())]

    def checkout(self, branch_or_commit_id: str) -> None:
        """
        Restores a variable state from commit_id.
        """
        ip = get_jupyter_kernel()
        if ip is None:
            raise ValueError("Jupyter kernel is unexpectedly None.")

        # By default, checkout at commit ID in detach mode.
        branch_name: Optional[str] = None
        commit_id = branch_or_commit_id
        is_detach = True

        # Attempt to interpret target as a branch.
        retrieved_branches = KishuBranch.get_branch(self._notebook_id, branch_or_commit_id)
        if len(retrieved_branches) == 1:
            assert retrieved_branches[0].branch_name == branch_or_commit_id
            branch_name = retrieved_branches[0].branch_name
            commit_id = retrieved_branches[0].commit_id
            is_detach = False

        # Retrieve checkout plan
        checkpoint_file = self.checkpoint_file()
        unit_exec_cell = UnitExecution.get_from_db(checkpoint_file, commit_id)
        if unit_exec_cell is None:
            raise ValueError("No commit entry found for commit_id = {}".format(commit_id))
        commit_entry = cast(CommitEntry, unit_exec_cell)
        if commit_entry.restore_plan is None:
            raise ValueError("No restore plan found for commit_id = {}".format(commit_id))

        # Restore notebook cells
        if commit_entry.raw_nb:
            self._checkout_notebook(commit_entry.raw_nb)

        # Restore user-namespace variables.
        user_ns = ip.user_ns   # will restore to global namespace
        target_ns: Dict[str, Any] = {}         # temp location
        commit_entry.restore_plan.run(target_ns, checkpoint_file, commit_id)
        self._checkout_namespace(user_ns, target_ns)

        # Update Kishu heads.
        self._graph.jump(commit_id)
        KishuBranch.update_head(
            self._notebook_id,
            branch_name=branch_name,
            commit_id=commit_id,
            is_detach=is_detach,
        )

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

        # Record variables in the user name prior to running cell.
        self._pre_run_cell_vars = set(self.get_user_namespace_vars())
        print("pre run cell vars:", self._pre_run_cell_vars)
        
        # Populate missing ID graph entries.
        for var in self._ahg.variable_snapshots.keys():
            if var not in self._id_graph_map and var in self._user_ns:
                self._id_graph_map[var] = idgraph.get_object_state(self._user_ns[var], {})

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
        entry.message = f"Auto-commit after executing <{short_raw_cell}>"

        # Jupyter-specific info for commit entry.
        entry.start_time_ms = self._start_time_ms
        entry.end_time_ms = get_epoch_time_ms()
        if entry.start_time_ms is not None:
            entry.runtime_ms = entry.end_time_ms - entry.start_time_ms
        entry.code_block = result.info.raw_cell
        entry.error_before_exec = repr_if_not_none(result.error_before_exec)
        entry.error_in_exec = repr_if_not_none(result.error_in_exec)
        entry.result = repr_if_not_none(result.result)

        # Find accessed variables.
        accessed_vars, _ = find_input_vars(entry.code_block, post_run_cell_vars,
                self._user_ns, set())

        # Find created and deleted variables.
        post_run_cell_vars = self.get_user_namespace_vars()
        created_vars, deleted_vars = find_created_and_deleted_vars(self._pre_run_cell_vars,
                post_run_cell_vars)

        # Find modified variables.
        modified_vars = set()
        for k in self._id_graph_map.keys():
            new_idgraph = idgraph.get_object_state(self._user_ns[k], {})
            if not idgraph.compare_id_graph(self._id_graph_map[k], new_idgraph):
                self._id_graph_map[k] = new_idgraph
                modified_vars.add(k)

        # Update AHG.
        if entry.start_time_ms is not None:
            self._ahg.update_graph(entry.code_block, entry.runtime_ms,
                    entry.start_time_ms, accessed_vars,
                    created_and_deleted_vars, modified_vars)
        else:
            self._ahg.update_graph(result.info.raw_cell, 0, 0, accessed_vars,
                    created_vars.union(modified_vars), deleted_vars)

        # Update ID graphs for newly created variables.
        for var in created_vars:
            self._id_graph_map[var] = idgraph.get_object_state(self._user_ns[var], {})

        # Step forward internal data.
        self._last_execution_count = result.execution_count
        self._start_time_ms = None

        self._commit_entry(entry)

    def record_connection(self) -> None:
        with open(KishuResource.connection_path(self._notebook_id), 'w') as f:
            f.write(JupyterConnectionInfo(  # type: ignore
                kernel_id=self._kernel_id,
                notebook_path=str(self._notebook_path),
            ).to_json())

    @staticmethod
    def retrieve_connection(notebook_id: str) -> Optional[JupyterConnectionInfo]:
        try:
            with open(KishuResource.connection_path(notebook_id), 'r') as f:
                json_str = f.read()
                return JupyterConnectionInfo.from_json(json_str)  # type: ignore
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return None

    def commit(self, message: Optional[str] = None) -> BareReprStr:
        entry = CommitEntry(kind=CommitEntryKind.manual)
        entry.execution_count = self._last_execution_count
        entry.message = message if message is not None else f"Manual commit after {entry.execution_count} executions."
        self._commit_entry(entry)
        return BareReprStr(entry.exec_id)

    def _commit_entry(self, entry: CommitEntry) -> None:
        # Generate commit ID/
        entry.exec_id = self._commit_id()

        # Force saving to observe all cells and extract notebook informations.
        self._save_notebook()
        entry.raw_nb, entry.formatted_cells = self._all_notebook_cells()

        # Plan for checkpointing and restoration.
        checkpoint_start_sec = time.time()
        restore = self._checkpoint(entry)
        entry.restore_plan = restore
        checkpoint_runtime_ms = round((time.time() - checkpoint_start_sec) * 1000)
        entry.checkpoint_runtime_ms = checkpoint_runtime_ms

        # Update other structures.
        self._history.append(entry)
        self._graph.step(entry.exec_id)
        self._step_branch(entry.exec_id)

    def _commit_id(self) -> str:
        if self._commit_id_mode == "counter":
            return str(self._session_id) + ":" + str(self._last_execution_count)
        return str(uuid.uuid4())[:8]  # TODO: Extend to whole UUID.

    def _checkpoint(self, cell_info: CommitEntry) -> RestorePlan:
        """
        Performs checkpointing and creates a matching restoration plan.

        TODO: Perform more intelligent checkpointing.
        """
        # Step 1: checkpoint
        ip = get_jupyter_kernel()
        user_ns = {} if ip is None else ip.user_ns
        checkpoint_file = self.checkpoint_file()
        exec_id = cell_info.exec_id
        var_names = [item[0] for item in filter(no_ipython_var, user_ns.items())]
        cell_info.checkpoint_vars = var_names

        # Step 2: invoke optimizer to compute restoration plan
        # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
        active_vss = set()
        for vs_list in self._ahg.variable_snapshots.values():
            if not vs_list[-1].deleted:
                active_vss.add(vs_list[-1])

        # Profile the size of each variable defined in the current session.
        for active_vs in active_vss:
            active_vs.size = profile_variable_size(user_ns[active_vs.name])

        # Initialize the optimizer. Migration speed is currently set to large value to prompt optimizer to store everything.
        optimizer = Optimizer(np.inf)
        optimizer.ahg = self._ahg
        optimizer.active_vss = active_vss

        # TODO: add overlap detection in the future.
        optimizer.linked_vs_pairs = set()

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.select_vss()

        checkpoint = StoreEverythingCheckpointPlan.create(user_ns, checkpoint_file, exec_id, var_names)
        checkpoint.run(user_ns)

        # Step 2: prepare a restoration plan using results from the optimizer.
        restore_plan = RestorePlan.create(self._ahg, vss_to_migrate, ces_to_recompute)
        print("commit id:", cell_info.exec_id)
        return restore_plan

    def _save_notebook(self) -> None:
        if self._notebook_path is None:
            return

        # Remember starting state.
        start_mtime = os.path.getmtime(self._notebook_path)
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
            current_mtime = os.path.getmtime(self._notebook_path)
            sleep_t *= 1.2
            time.sleep(sleep_t)
        if sleep_t >= 1.0:
            print("WARNING: Notebook saving is taking too long. Kishu may not capture every cell.")

    def _all_notebook_cells(self) -> Tuple[Optional[str], List[FormattedCell]]:
        if self._notebook_path is None:
            return None, []

        with open(self._notebook_path, 'r') as f:
            nb = nbformat.read(f, KishuForJupyter.NBFORMAT_VERSION)

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
        head = KishuBranch.update_head(self._notebook_id, commit_id=commit_id)
        if head.branch_name is not None:
            KishuBranch.upsert_branch(self._notebook_id, head.branch_name, commit_id)

    def _checkout_notebook(self, raw_nb: str) -> None:
        if self._notebook_path is None:
            return

        # Read current notebook cells.
        with open(self._notebook_path, 'r') as f:
            nb = nbformat.read(f, KishuForJupyter.NBFORMAT_VERSION)

        # Apply target cells.
        target_nb = nbformat.reads(raw_nb, KishuForJupyter.NBFORMAT_VERSION)
        nb.cells = target_nb.cells

        # Save change
        nbformat.write(nb, self._notebook_path)

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
KISHU_VARS = set(['kishu', 'load_kishu'])


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


# Set when kishu_for_jupyter() is invoked within Jupyter. Interestingly, simply calling
# get_ipython() does not always access the globally accessible function; thus, we are taking this
# approach.
_ipython_shell = None


def get_jupyter_kernel():
    return _ipython_shell


# The singleton instance for execution history.
_kishu_exec_history: Optional[KishuForJupyter] = None


def get_kishu_instance():
    return _kishu_exec_history


KISHU_VAR_NAME = '_kishu'


def load_kishu(notebook_id: Optional[str] = None, session_id: Optional[int] = None) -> None:
    global _kishu_exec_history
    global _ipython_shell
    if _kishu_exec_history is not None:
        return
    _ipython_shell = eval('get_ipython()')
    ip = _ipython_shell
    kishu = None
    kishu = KishuForJupyter(notebook_id)
    _kishu_exec_history = kishu
    if session_id:
        kishu.set_session_id(session_id)
    ip.events.register('pre_run_cell', kishu.pre_run_cell)
    ip.events.register('post_run_cell', kishu.post_run_cell)
    ip.user_ns[KISHU_VAR_NAME] = kishu

    print("Kishu will now trace cell executions automatically.\n"
          "- You can inspect traced information using '_kishu'.\n"
          "- Checkpoint file: {}/\n".format(kishu.checkpoint_file()))


def update_metadata(nb: Any, nb_path: Path) -> None:
    if "kishu" not in nb.metadata:
        notebook_name = datetime.now().strftime('%Y%m%dT%H%M%S')
        nb["metadata"]["kishu"] = {}
        nb["metadata"]["kishu"]["notebook_id"] = notebook_name
    if "session_count" in nb.metadata.kishu:
        nb["metadata"]["kishu"]["session_count"] = nb["metadata"]["kishu"]["session_count"] + 1
    else:
        nb["metadata"]["kishu"]["session_count"] = 1
    nbformat.write(nb, nb_path)


def init_kishu(path: Optional[Path] = None) -> None:
    """
    If notebook not already initialized, initializes by adding notebook id to metadata
    Increments session number to ensure unique commit ids.
    """
    # Read enclosing notebook.
    if path is None:
        kernel_id = enclosing_kernel_id()
        path = enclosing_notebook_path(kernel_id)
    nb = None
    assert path is not None
    with open(path, 'r') as f:
        nb = nbformat.read(f, KishuForJupyter.NBFORMAT_VERSION)

    # Update notebook metadata.
    update_metadata(nb, path)

    # Attach Kishu instrumentation.
    load_kishu(nb.metadata.kishu.notebook_id, nb.metadata.kishu.session_count)
