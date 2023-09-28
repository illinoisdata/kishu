import pytest
import dataclasses
from typing import Generator, List, Optional, Type

from kishu.resources import KishuResource
from kishu.jupyterint2 import CommitEntryKind, CommitEntry, KishuForJupyter
from kishu.commit_graph import CommitNodeInfo
from kishu.commands import CommitSummary, KishuCommand, SelectedCommit


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
    kishu_jupyter.set_test_mode()
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

    yield ["0:1", "0:2", "0:3"]  # List of commit IDs


@dataclasses.dataclass
class JupyterInfoMock:
    raw_cell: Optional[str] = None


@dataclasses.dataclass
class JupyterResultMock:
    info: JupyterInfoMock = dataclasses.field(default_factory=JupyterInfoMock)
    execution_count: Optional[int] = None
    error_before_exec: Optional[str] = None
    error_in_exec: Optional[str] = None
    result: Optional[str] = None


class TestKishuCommand:

    def test_log(self, notebook_id, basic_execution_ids):
        log_result = KishuCommand.log(notebook_id, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_result.commit_graph[0].message,  # Not tested
            code_block="y = x + 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            code_block="y = 2",
            runtime_ms=log_result.commit_graph[1].runtime_ms,  # Not tested
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_result.commit_graph[2].message,  # Not tested
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[2].runtime_ms,  # Not tested
        )

        log_result = KishuCommand.log(notebook_id, basic_execution_ids[0])
        assert len(log_result.commit_graph) == 1
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
        )

    def test_log_all(self, notebook_id, basic_execution_ids):
        log_all_result = KishuCommand.log_all(notebook_id)
        assert len(log_all_result.commit_graph) == 3
        assert log_all_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_all_result.commit_graph[0].message,  # Not tested
            code_block="x = 1",
            runtime_ms=log_all_result.commit_graph[0].runtime_ms,  # Not tested
        )
        assert log_all_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_all_result.commit_graph[1].message,  # Not tested
            code_block="y = 2",
            runtime_ms=log_all_result.commit_graph[1].runtime_ms,  # Not tested
        )
        assert log_all_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_all_result.commit_graph[2].message,  # Not tested
            code_block="y = x + 1",
            runtime_ms=log_all_result.commit_graph[2].runtime_ms,  # Not tested
        )

    def test_status(self, notebook_id, basic_execution_ids):
        status_result = KishuCommand.status(notebook_id, basic_execution_ids[-1])
        assert status_result.commit_node_info == CommitNodeInfo(
            commit_id="0:3",
            parent_id="0:2",
        )
        assert status_result.commit_entry == CommitEntry(
            kind=CommitEntryKind.jupyter,
            exec_id="0:3",
            execution_count=3,
            code_block="y = x + 1",
            checkpoint_vars=[],
            ahg_string = status_result.commit_entry.ahg_string, # Not tested
            message=status_result.commit_entry.message,  # Not tested,
            start_time_ms=status_result.commit_entry.start_time_ms,  # Not tested
            end_time_ms=status_result.commit_entry.end_time_ms,  # Not tested
            checkpoint_runtime_ms=status_result.commit_entry.checkpoint_runtime_ms,  # Not tested
            runtime_ms=status_result.commit_entry.runtime_ms,  # Not tested
            raw_nb=status_result.commit_entry.raw_nb,  # Not tested
            formatted_cells=status_result.commit_entry.formatted_cells,  # Not tested
            restore_plan=status_result.commit_entry.restore_plan,  # Not tested
        )

    def test_branch(self, notebook_id, basic_execution_ids):
        branch_result = KishuCommand.branch(notebook_id, "at_head", None)
        assert branch_result.status == "ok"

        branch_result = KishuCommand.branch(notebook_id, "historical", basic_execution_ids[1])
        assert branch_result.status == "ok"

    def test_fe_commit_graph(self, notebook_id, basic_execution_ids):
        fe_commit_graph_result = KishuCommand.fe_commit_graph(notebook_id)
        assert len(fe_commit_graph_result.commits) == 3

    def test_fe_commit(self, notebook_id, basic_execution_ids):
        fe_commit_result = KishuCommand.fe_commit(notebook_id, basic_execution_ids[-1], vardepth=0)
        assert fe_commit_result == SelectedCommit(
            oid="0:3",
            parent_oid="0:2",
            timestamp=fe_commit_result.timestamp,  # Not tested
            latest_exec_num="3",
            cells=fe_commit_result.cells,  # Not tested
            variables=[],
        )
