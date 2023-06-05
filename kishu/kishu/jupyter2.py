"""
Kishu-Jupyter Integration Module (2nd version)

# Basic Usage

```
from kishu import register_kishu
register_kishu(get_ipython())

Reference
- https://ipython.readthedocs.io/en/stable/config/callbacks.html
```

Then, all the cell executions are recorded, and the result of each cell execution is checkpointed.
"""
import json
import time
import dataclasses
from dataclasses import dataclass
from typing import List, Any

from .exec import UnitExecution


@dataclass
class CellExecInfo(UnitExecution):
    """
    Records the information related to Jupyter's cell execution.

    @param raw_cell  The original statements (in str) within a cell.
    @param execution_count  The ipython-tracked execution count, which is used for displaying
                            the cell number on Jupyter.
    @param start_time_ms  The epoch time in milliseconds. Obtained by round(time.time()*1000).
            start_time_ms=None means that the start time is unknown, which is the case when
            the callback is first registered.
    @param accessed_variables  All the global variables read-accessed within a cell. If there
            are function calls accessing them, they must be included.
    """
    execution_count: int = None
    error_before_exec: str = None
    error_in_exec: str = None
    result: Any = None
    start_time_ms: int = None


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    Taken from https://stackoverflow.com/questions/51286748/make-the-python-json-encoder-support-pythons-new-dataclasses
    """
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class KishuJupyterExecHistory:

    history: List[CellExecInfo]
    _running_cell: CellExecInfo
    

    def __init__(self, ip) -> None:
        """
        @param ip  An instance from get_ipython(), which is typically an instance of the 
                   `ZMQInteractiveShell` class.
        """
        self.shell = ip
        self.history = []
        self._running_cell = None

    def __repr__(self) -> str:
        return json.dumps(self.history, cls=EnhancedJSONEncoder, sort_keys=True, indent=2)

    def pre_run_cell(self, info) -> None:
        """
        Invoked before running a cell.

        Example:
        print('info.raw_cell =', info.raw_cell)
        print('info.store_history =', info.store_history)
        print('info.silent =', info.silent)
        print('info.shell_futures =', info.shell_futures)
        print('info.cell_id =', info.cell_id)
        print(dir(info))
        """
        cell_info = CellExecInfo()
        cell_info.start_time_ms = round(time.time() * 1000)
        self._running_cell = cell_info

    def post_run_cell(self, result) -> None:
        """
        print('result.execution_count = ', result.execution_count)
        print('result.error_before_exec = ', result.error_before_exec)
        print('result.error_in_exec = ', result.error_in_exec)
        print('result.info = ', result.info)
        print('result.result = ', result.result)
        """
        # running_cell may be None for the first time this callback is registered.
        cell_info = CellExecInfo() if self._running_cell is None else self._running_cell
        cell_info.code_block = result.info.raw_cell
        cell_info.execution_count = result.execution_count
        cell_info.error_before_exec = result.error_before_exec
        cell_info.error_in_exec = result.error_in_exec
        cell_info.result = result.result
        # TODO: set modified variables
        # TODO: may want to perform checkpointing
        self.history.append(cell_info)
        self._running_cell = None


def register_kishu(ip) -> KishuJupyterExecHistory:
    history = KishuJupyterExecHistory(ip)
    ip.events.register('pre_run_cell', history.pre_run_cell)
    ip.events.register('post_run_cell', history.post_run_cell)
    return history
