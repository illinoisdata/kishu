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
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, cast

from kishu.checkpoint_io import init_checkpoint_database
from kishu.commit_graph import KishuCommitGraph
from kishu.resources import KishuResource

from .plan import ExecutionHistory, StoreEverythingCheckpointPlan, UnitExecution, RestorePlan


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
    _restore_plan: Optional[RestorePlan] = None


class KishuForJupyter:
    CURRENT_CELL_ID = 'current'

    def __init__(self, notebook_id: Optional[str] = None) -> None:
        """
        @param _history  The connector to log data.
        @param _running_cell  A temporary data created during a cell execution.
        @param _checkpoint_file  The file for storing all the data.
        """
        if notebook_id is None:
            self._notebook_id = datetime.now().strftime('%Y%m%dT%H%M%S')  # TODO: notebook name.
        else:
            self._notebook_id = notebook_id
        self._running_cell: Optional[CellExecInfo] = None
        init_checkpoint_database(self.checkpoint_file())
        self._history: ExecutionHistory = ExecutionHistory(self.checkpoint_file())
        self._graph: KishuCommitGraph = KishuCommitGraph.new_on_file(
            KishuResource.commit_graph_directory(self._notebook_id)
        )

    def log(self) -> ExecutionHistory:
        return self._history

    def checkpoint_file(self) -> str:
        return KishuResource.checkpoint_path(self._notebook_id)

    def checkout(self, checkpoint_file: str, commit_id: str) -> None:
        """
        Restores a variable state from commit_id.
        """
        ip = get_jupyter_kernel()
        if ip is None:
            raise ValueError("Jupyter kernel is unexpectedly None.")
        commit_id = str(commit_id)

        # read checkout plan
        cell = cast(CellExecInfo, UnitExecution.get_from_db(checkpoint_file, commit_id))
        restore_plan: Optional[RestorePlan] = cell._restore_plan
        if restore_plan is None:
            raise ValueError("No restore plan found for commit_id = {}".format(commit_id))

        # perform checkout
        user_ns = ip.user_ns   # will restore to global namespace
        target_ns: Dict[str, Any] = {}         # temp location
        restore_plan.run(target_ns, checkpoint_file, commit_id)
        user_ns.update(target_ns)
        print('Checked-out variables: {}'.format(list(target_ns.keys())))
        # TODO: update execution count and database history

        # update kishu internal state
        self._graph.jump(commit_id)

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

        # checkpointing
        checkpoint_start_sec = time.time()
        restore = self._checkpoint(cell_info)
        cell_info._restore_plan = restore
        checkpoint_runtime_ms = round((time.time() - checkpoint_start_sec) * 1000)
        cell_info.checkpoint_runtime_ms = checkpoint_runtime_ms

        # epilogue
        self._history.append(cell_info)
        self._graph.step(cell_info.exec_id)
        self._running_cell = None

    def _commit_id(self, result) -> str:
        return str(result.execution_count)

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


def load_kishu() -> None:
    global _kishu_exec_history
    global _ipython_shell
    if _kishu_exec_history is not None:
        return
    _ipython_shell = eval('get_ipython()')
    ip = _ipython_shell

    kishu = KishuForJupyter()
    _kishu_exec_history = kishu
    ip.events.register('pre_run_cell', kishu.pre_run_cell)
    ip.events.register('post_run_cell', kishu.post_run_cell)
    ip.user_ns[KISHU_VAR_NAME] = kishu
    print("Kishu will now trace cell executions automatically.\n"
          "- You can inspect traced information using '_kishu'.\n"
          "- Checkpoint file: {}/\n".format(kishu.checkpoint_file()))
