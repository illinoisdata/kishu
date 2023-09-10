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
import ipykernel
import ipylab
import IPython
import json
import jupyter_core.paths
import nbformat
import os
import time
import urllib.request
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
from kishu.resources import KishuResource

from .plan import ExecutionHistory, StoreEverythingCheckpointPlan, UnitExecution, RestorePlan


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


"""
Notebook instrument.
"""


@dataclass
class NBFormatCell:
    cell_type: str
    source: str
    output: Optional[str]
    execution_count: Optional[int]


@dataclass
class CellExecInfo(UnitExecution):
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
    @param _restore_plan  The checkpoint algorithm also sets this restoration plan, which
            when executed, restores all the variables as they are.
    """
    execution_count: Optional[int] = None
    error_before_exec: Optional[str] = None
    error_in_exec: Optional[str] = None
    result: Optional[str] = None
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None
    runtime_ms: Optional[int] = None
    checkpoint_runtime_ms: Optional[int] = None
    checkpoint_vars: Optional[List[str]] = None
    executed_cells: Optional[List[NBFormatCell]] = None
    _restore_plan: Optional[RestorePlan] = None


@dataclass_json
@dataclass
class JupyterConnection:
    kernel_id: str
    notebook_path: str


class KishuForJupyter:
    CURRENT_CELL_ID = 'current'
    SAVE_CMD = "try { IPython.notebook.save_checkpoint(); } catch { }"

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
        self._running_cell: Optional[CellExecInfo] = None
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

        self._platform = enclosing_platform()
        self._session_id = 0
    
    def set_session_id(self, session_id):
        self._session_id = session_id

    def log(self) -> ExecutionHistory:
        return self._history

    def checkpoint_file(self) -> str:
        return KishuResource.checkpoint_path(self._notebook_id)

    def checkout(self, commit_id: str) -> None:
        """
        Restores a variable state from commit_id.
        """
        ip = get_jupyter_kernel()
        if ip is None:
            raise ValueError("Jupyter kernel is unexpectedly None.")
        commit_id = str(commit_id)

        # read checkout plan
        checkpoint_file = self.checkpoint_file()
        cell = cast(CellExecInfo, UnitExecution.get_from_db(checkpoint_file, commit_id))
        restore_plan: Optional[RestorePlan] = cell._restore_plan
        if restore_plan is None:
            raise ValueError("No restore plan found for commit_id = {}".format(commit_id))

        # perform checkout
        user_ns = ip.user_ns   # will restore to global namespace
        target_ns: Dict[str, Any] = {}         # temp location
        restore_plan.run(target_ns, checkpoint_file, commit_id)
        self._apply_namespace(user_ns, target_ns)
        print('Checked-out variables: {}'.format(list(target_ns.keys())))
        # TODO: update execution count and database history

        # update kishu internal state
        self._graph.jump(commit_id)

        # update branch head.
        KishuBranch.update_head(self._notebook_id, commit_id=commit_id, is_detach=True)

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
        cell_info = CellExecInfo()
        cell_info.start_time_ms = get_epoch_time_ms()
        cell_info.exec_id = KishuForJupyter.CURRENT_CELL_ID
        cell_info.code_block = info.raw_cell
        # self.history.append(cell_info)
        self._running_cell = cell_info
        cell_info.current_time = datetime.now()

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
        # Force saving to observe all cells.
        self._save_notebook()

        # running_cell may be None for the first time this callback is registered.
        cell_info = CellExecInfo() if self._running_cell is None else self._running_cell
        cell_info.end_time_ms = get_epoch_time_ms()
        if cell_info.start_time_ms is not None:
            cell_info.runtime_ms = cell_info.end_time_ms - cell_info.start_time_ms
        cell_info.code_block = result.info.raw_cell
        cell_info.execution_count = result.execution_count
        cell_info.exec_id = self._commit_id(result)
        cell_info.error_before_exec = repr_if_not_none(result.error_before_exec)
        cell_info.error_in_exec = repr_if_not_none(result.error_in_exec)
        cell_info.result = repr_if_not_none(result.result)
        cell_info.executed_cells = self._all_notebook_cells()

        # checkpointing
        checkpoint_start_sec = time.time()
        restore = self._checkpoint(cell_info)
        cell_info._restore_plan = restore
        checkpoint_runtime_ms = round((time.time() - checkpoint_start_sec) * 1000)
        cell_info.checkpoint_runtime_ms = checkpoint_runtime_ms

        # epilogue
        self._history.append(cell_info)
        self._graph.step(cell_info.exec_id)
        self._step_branch(cell_info.exec_id)
        self._running_cell = None

    def record_connection(self) -> None:
        with open(KishuResource.connection_path(self._notebook_id), 'w') as f:
            f.write(JupyterConnection(  # type: ignore
                kernel_id=self._kernel_id,
                notebook_path=str(self._notebook_path),
            ).to_json())

    @staticmethod
    def retrieve_connection(notebook_id: str) -> Optional[JupyterConnection]:
        try:
            with open(KishuResource.connection_path(notebook_id), 'r') as f:
                json_str = f.read()
                return JupyterConnection.from_json(json_str)  # type: ignore
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return None

    def _commit_id(self, result) -> str:
        return str(self._session_id) + ":" + str(result.execution_count)

    def _checkpoint(self, cell_info: CellExecInfo) -> RestorePlan:
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
        checkpoint = StoreEverythingCheckpointPlan.create(user_ns, checkpoint_file, exec_id, var_names)
        checkpoint.run(user_ns)

        # Step 2: prepare a restoration plan
        restore: RestorePlan = checkpoint.restore_plan()
        return restore

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

    def _all_notebook_cells(self) -> List[NBFormatCell]:
        if self._notebook_path is None:
            return []

        with open(self._notebook_path, 'r') as f:
            nb = nbformat.read(f, 4)

        nb_cells = []
        for cell in nb.cells:
            if cell.cell_type == "code":
                nb_cells.append(NBFormatCell(
                    cell_type=cell.cell_type,
                    source=cell.source,
                    output=self._parse_cell_output(cell.outputs),
                    execution_count=cell.execution_count,
                ))
            elif cell.cell_type == "markdown":
                nb_cells.append(NBFormatCell(
                    cell_type=cell.cell_type,
                    source=cell.source,
                    output=None,
                    execution_count=None,
                ))
            else:
                raise ValueError(f"Unknown cell type: {cell.cell_type}")
        return nb_cells

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

    def _apply_namespace(self, user_ns: Dict[Any, Any], target_ns: Dict[Any, Any]) -> None:
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


def get_executed_cells():
    ip = get_jupyter_kernel()
    if ip is None:
        return None
    return ip.user_ns["In"]


# The singleton instance for execution history.
_kishu_exec_history: Optional[KishuForJupyter] = None


def get_kishu_instance():
    return _kishu_exec_history


KISHU_VAR_NAME = '_kishu'


def load_kishu(notebook_id=None, session_id=None) -> None:
    global _kishu_exec_history
    global _ipython_shell
    if _kishu_exec_history is not None:
        return
    _ipython_shell = eval('get_ipython()')
    ip = _ipython_shell
    kishu = None
    if notebook_id:
        kishu = KishuForJupyter(notebook_id)
    else:
        kishu = KishuForJupyter()
    _kishu_exec_history = kishu
    if session_id:
        kishu.set_session_id(session_id)
    ip.events.register('pre_run_cell', kishu.pre_run_cell)
    ip.events.register('post_run_cell', kishu.post_run_cell)
    ip.user_ns[KISHU_VAR_NAME] = kishu

    print("Kishu will now trace cell executions automatically.\n"
          "- You can inspect traced information using '_kishu'.\n"
          "- Checkpoint file: {}/\n".format(kishu.checkpoint_file()))

def init_kishu() -> None:
    """
    If notebook not already initialized, initializes by adding notebook id to metadata
    Increments session number to ensure unique commit ids.
    """
    kernel_id = enclosing_kernel_id()
    path = enclosing_notebook_path(kernel_id)
    nb = None
    with open(path, 'r') as f:
        nb = nbformat.read(f, 4)
    if "notebook_id" not in nb.metadata:
        print("Adding kishu to notebook")
        notebook_name = datetime.now().strftime('%Y%m%dT%H%M%S')
        nb["metadata"]["notebook_id"] = notebook_name
        nb["metadata"]["session_count"] = 1
        nbformat.write(nb, path)
    else:
        print("already initialized")
        if "session_count" in nb.metadata:
            nb["metadata"]["session_count"] = nb["metadata"]["session_count"] + 1
        else:
            nb["metadata"]["session_count"] = 1
        nbformat.write(nb, path)
    load_kishu(nb.metadata["notebook_id"], nb.metadata["session_count"])
    

    
        

