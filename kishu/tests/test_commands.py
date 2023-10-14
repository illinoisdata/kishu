import dataclasses
import pytest

from typing import Generator, List, Optional

from kishu.commands import CommitSummary, FECommit, FESelectedCommit, KishuCommand, KishuSession
from kishu.jupyterint import CommitEntryKind, CommitEntry, KishuForJupyter
from kishu.notebook_id import NotebookId
from kishu.storage.branch import KishuBranch
from kishu.storage.commit_graph import CommitNodeInfo
from tests.helpers.utils_for_test import environment_variable

@pytest.fixture()
def notebook_id() -> Generator[str, None, None]:
    yield "notebook_123"


@pytest.fixture()
def kishu_jupyter(tmp_kishu_path, notebook_id) -> Generator[KishuForJupyter, None, None]:
    with environment_variable("notebook_path", "None"):
        kishu_jupyter = KishuForJupyter(notebook_id=NotebookId.from_key(notebook_id))
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

    def test_list(self, notebook_id, basic_execution_ids):
        list_result = KishuCommand.list()
        assert len(list_result.sessions) == 0

        # TODO: Test with alive sessions.
        list_result = KishuCommand.list(list_all=True)
        assert len(list_result.sessions) == 1
        assert list_result.sessions[0] == KishuSession(
            notebook_id=notebook_id,
            kernel_id=None,
            notebook_path="None",
            is_alive=False,
        )

    def test_log(self, notebook_id, basic_execution_ids):
        log_result = KishuCommand.log(notebook_id, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            code_block="y = 2",
            runtime_ms=log_result.commit_graph[1].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            code_block="y = x + 1",
            runtime_ms=log_result.commit_graph[2].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )

        log_result = KishuCommand.log(notebook_id, basic_execution_ids[0])
        assert len(log_result.commit_graph) == 1
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )

    def test_log_all(self, notebook_id, basic_execution_ids):
        log_all_result = KishuCommand.log_all(notebook_id)
        assert len(log_all_result.commit_graph) == 3
        assert log_all_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_all_result.commit_graph[0].message,  # Not tested
            timestamp=log_all_result.commit_graph[0].timestamp,  # Not tested
            code_block="x = 1",
            runtime_ms=log_all_result.commit_graph[0].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_all_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_all_result.commit_graph[1].message,  # Not tested
            timestamp=log_all_result.commit_graph[1].timestamp,  # Not tested
            code_block="y = 2",
            runtime_ms=log_all_result.commit_graph[1].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_all_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_all_result.commit_graph[2].message,  # Not tested
            timestamp=log_all_result.commit_graph[2].timestamp,  # Not tested
            code_block="y = x + 1",
            runtime_ms=log_all_result.commit_graph[2].runtime_ms,  # Not tested
            branches=[],
            tags=[],
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
            message=status_result.commit_entry.message,  # Not tested,
            timestamp_ms=status_result.commit_entry.timestamp_ms,  # Not tested
            ahg_string=status_result.commit_entry.ahg_string,  # Not tested
            code_version=status_result.commit_entry.code_version,  # Not tested
            var_version=status_result.commit_entry.var_version,  # Not tested
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

    def test_branch_log(self, notebook_id, basic_execution_ids):
        _ = KishuCommand.branch(notebook_id, "at_head", None)
        _ = KishuCommand.branch(notebook_id, "historical", basic_execution_ids[1])
        log_result = KishuCommand.log(notebook_id, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            code_block="y = 2",
            runtime_ms=log_result.commit_graph[1].runtime_ms,  # Not tested
            branches=["historical"],
            tags=[],
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            code_block="y = x + 1",
            runtime_ms=log_result.commit_graph[2].runtime_ms,  # Not tested
            branches=["at_head"],
            tags=[],
        )

    def test_rename_branch_basic(self, notebook_id, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(notebook_id, branch_1, None)

        rename_branch_result = KishuCommand.rename_branch(
            notebook_id, branch_1, "new_branch")
        head = KishuBranch.get_head(notebook_id)
        assert rename_branch_result.status == "ok"
        assert head.branch_name == "new_branch"

    def test_rename_branch_non_existing_branch(
            self, notebook_id, basic_execution_ids):
        rename_branch_result = KishuCommand.rename_branch(
            notebook_id, "non_existing_branch", "new_branch")
        assert rename_branch_result.status == "error"

    def test_rename_branch_new_repeating_branch(
            self, notebook_id, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(notebook_id, branch_1, None)

        rename_branch_result = KishuCommand.rename_branch(
            notebook_id, branch_1, branch_1)
        assert rename_branch_result.status == "error"

    def test_tag(self, notebook_id, basic_execution_ids):
        tag_result = KishuCommand.tag(notebook_id, "at_head", None, "In current time")
        assert tag_result.status == "ok"
        assert tag_result.tag_name == "at_head"
        assert tag_result.commit_id == basic_execution_ids[-1]
        assert tag_result.message == "In current time"

        tag_result = KishuCommand.tag(notebook_id, "historical", basic_execution_ids[1], "")
        assert tag_result.status == "ok"
        assert tag_result.tag_name == "historical"
        assert tag_result.commit_id == basic_execution_ids[1]
        assert tag_result.message == ""

    def test_tag_log(self, notebook_id, basic_execution_ids):
        _ = KishuCommand.tag(notebook_id, "at_head", None, "In current time")
        _ = KishuCommand.tag(notebook_id, "historical", basic_execution_ids[1], "")
        log_result = KishuCommand.log(notebook_id, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            code_block="x = 1",
            runtime_ms=log_result.commit_graph[0].runtime_ms,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            code_block="y = 2",
            runtime_ms=log_result.commit_graph[1].runtime_ms,  # Not tested
            branches=[],
            tags=["historical"],
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            code_block="y = x + 1",
            runtime_ms=log_result.commit_graph[2].runtime_ms,  # Not tested
            branches=[],
            tags=["at_head"],
        )

    def test_fe_commit_graph(self, notebook_id, basic_execution_ids):
        fe_commit_graph_result = KishuCommand.fe_commit_graph(notebook_id)
        assert len(fe_commit_graph_result.commits) == 3

    def test_fe_commit(self, notebook_id, basic_execution_ids):
        fe_commit_result = KishuCommand.fe_commit(notebook_id, basic_execution_ids[-1], vardepth=0)
        assert fe_commit_result == FESelectedCommit(
            commit=FECommit(
                oid="0:3",
                parent_oid="0:2",
                timestamp=fe_commit_result.commit.timestamp,  # Not tested
                branches=[],
                tags=[],
                code_version=fe_commit_result.commit.code_version,  # Not tested
                var_version=fe_commit_result.commit.var_version,  # Not tested
            ),
            executed_cells=[  # TODO: Missing due to missing IPython kernel.
                # "x = 1",
                # "y = 2",
                # "y = x + 1",
            ],
            cells=fe_commit_result.cells,  # Not tested
            variables=[],
        )
