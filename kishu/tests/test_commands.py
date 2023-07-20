import pytest
import dataclasses
from typing import Generator, List, Optional, Type

from kishu.resources import KishuResource
from kishu.jupyterint2 import CellExecInfo, KishuForJupyter
from kishu.commit_graph import CommitInfo
from kishu.commands import CommitSummary, KishuCommand, SelectedHistory


@pytest.fixture()
def kishu_resource(tmp_path) -> Generator[Type[KishuResource], None, None]:
    original_root = KishuResource.ROOT
    KishuResource.ROOT = tmp_path
    yield KishuResource
    KishuResource.ROOT = original_root


@pytest.fixture()
def notebook_id() -> Generator[str, None, None]:
    yield "notebook_123"


@pytest.fixture()
def kishu_jupyter(kishu_resource, notebook_id) -> Generator[KishuForJupyter, None, None]:
    kishu_jupyter = KishuForJupyter(notebook_id=notebook_id)
    yield kishu_jupyter


@pytest.fixture()
def basic_execution_ids(kishu_jupyter) -> Generator[List[str], None, None]:
    execution_count = 1
    info = JupyterInfoMock(raw_cell="x = 1")
    kishu_jupyter.pre_run_cell(info)
    kishu_jupyter.post_run_cell(JupyterResultMock(info=info, execution_count=execution_count))
    execution_count = 2
    info = JupyterInfoMock(raw_cell="y = 2")
    kishu_jupyter.pre_run_cell(info)
    kishu_jupyter.post_run_cell(JupyterResultMock(info=info, execution_count=execution_count))
    execution_count = 3
    info = JupyterInfoMock(raw_cell="y = x + 1")
    kishu_jupyter.pre_run_cell(info)
    kishu_jupyter.post_run_cell(JupyterResultMock(info=info, execution_count=execution_count))

    yield ["1", "2", "3"]  # List of commit IDs


@dataclasses.dataclass
class JupyterInfoMock:
    raw_cell: Optional[str] = None


@dataclasses.dataclass
class JupyterResultMock:
    info: JupyterInfoMock = JupyterInfoMock()
    execution_count: Optional[int] = None
    error_before_exec: Optional[str] = None
    error_in_exec: Optional[str] = None
    result: Optional[str] = None


class TestKishuCommand:

    def test_log(self, notebook_id, basic_execution_ids):
        log_result = KishuCommand.log(notebook_id, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="3",
            parent_id="2",
            code_block="y = x + 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="2",
            parent_id="1",
            code_block="y = 2",
            runtime_ms=log_result.commit_graph[1].runtime_ms,  # Not tested
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="1",
            parent_id="",
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[2].runtime_ms,  # Not tested
        )

        log_result = KishuCommand.log(notebook_id, basic_execution_ids[0])
        assert len(log_result.commit_graph) == 1
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="1",
            parent_id="",
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
        )

    def test_log_all(self, notebook_id, basic_execution_ids):
        log_all_result = KishuCommand.log_all(notebook_id)
        assert len(log_all_result.commit_graph) == 3
        assert log_all_result.commit_graph[0] == CommitSummary(
            commit_id="1",
            parent_id="",
            code_block="x = 1",
            runtime_ms=log_all_result.commit_graph[0].runtime_ms,  # Not tested
        )
        assert log_all_result.commit_graph[1] == CommitSummary(
            commit_id="2",
            parent_id="1",
            code_block="y = 2",
            runtime_ms=log_all_result.commit_graph[1].runtime_ms,  # Not tested
        )
        assert log_all_result.commit_graph[2] == CommitSummary(
            commit_id="3",
            parent_id="2",
            code_block="y = x + 1",
            runtime_ms=log_all_result.commit_graph[2].runtime_ms,  # Not tested
        )

    def test_status(self, notebook_id, basic_execution_ids):
        status_result = KishuCommand.status(notebook_id, basic_execution_ids[-1])
        assert status_result.commit_info == CommitInfo(
            commit_id="3",
            parent_id="2",
        )
        assert status_result.cell_exec_info == CellExecInfo(
            exec_id="3",
            execution_count=3,
            code_block="y = x + 1",
            checkpoint_vars=[],
            start_time_ms=status_result.cell_exec_info.start_time_ms,  # Not tested
            end_time_ms=status_result.cell_exec_info.end_time_ms,  # Not tested
            checkpoint_runtime_ms=status_result.cell_exec_info.checkpoint_runtime_ms,  # Not tested
            runtime_ms=status_result.cell_exec_info.runtime_ms,  # Not tested
            _restore_plan=status_result.cell_exec_info._restore_plan,  # Not tested
        )

    def test_fe_initialize(self, notebook_id, basic_execution_ids):
        fe_initialize_result = KishuCommand.fe_initialize(notebook_id)
        assert len(fe_initialize_result.histories) == 3

    def test_fe_history(self, notebook_id, basic_execution_ids):
        fe_history_result = KishuCommand.fe_history(notebook_id, basic_execution_ids[-1])
        assert fe_history_result == SelectedHistory(
            oid="3",
            timestamp=fe_history_result.timestamp,  # Not tested
            exec_cell="y = x + 1",
            variables=[],
        )
