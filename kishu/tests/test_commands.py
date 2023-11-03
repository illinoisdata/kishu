import os
import pytest

from pathlib import Path
from typing import List

from tests.helpers.nbexec import KISHU_INIT_STR

from kishu.commands import CommitSummary, FECommit, FESelectedCommit, KishuCommand, KishuSession
from kishu.jupyterint import CommitEntryKind, CommitEntry
from kishu.runtime import JupyterRuntimeEnv
from kishu.storage.branch import KishuBranch
from kishu.storage.commit_graph import CommitNodeInfo


class TestKishuCommand:
    def test_list(self, set_notebook_path_env, notebook_key, basic_execution_ids):
        list_result = KishuCommand.list()
        assert len(list_result.sessions) == 0

        # TODO: Test with alive sessions.
        list_result = KishuCommand.list(list_all=True)
        assert len(list_result.sessions) == 1
        assert list_result.sessions[0] == KishuSession(
            notebook_key=notebook_key,
            kernel_id="test_kernel_id",
            notebook_path=os.environ.get("TEST_NOTEBOOK_PATH"),
            is_alive=False,
        )

    def test_log(self, notebook_key, basic_execution_ids):
        log_result = KishuCommand.log(notebook_key, basic_execution_ids[-1])
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
            branches=["auto_0:1"],
            tags=[],
        )

        log_result = KishuCommand.log(notebook_key, basic_execution_ids[0])
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

    def test_log_all(self, notebook_key, basic_execution_ids):
        log_all_result = KishuCommand.log_all(notebook_key)
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
            branches=["auto_0:1"],
            tags=[],
        )

    def test_status(self, notebook_key, basic_execution_ids):
        status_result = KishuCommand.status(notebook_key, basic_execution_ids[-1])
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

    def test_branch(self, notebook_key, basic_execution_ids):
        branch_result = KishuCommand.branch(notebook_key, "at_head", None)
        assert branch_result.status == "ok"

        branch_result = KishuCommand.branch(notebook_key, "historical", basic_execution_ids[1])
        assert branch_result.status == "ok"

    def test_branch_log(self, notebook_key, basic_execution_ids):
        _ = KishuCommand.branch(notebook_key, "at_head", None)
        _ = KishuCommand.branch(notebook_key, "historical", basic_execution_ids[1])
        log_result = KishuCommand.log(notebook_key, basic_execution_ids[-1])
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
            branches=["auto_0:1", "at_head"],
            tags=[],
        )

    def test_delete_basic(self, notebook_key, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(notebook_key, branch_1, basic_execution_ids[1])

        delete_result = KishuCommand.delete_branch(notebook_key, branch_1)
        assert delete_result.status == "ok"

        log_result = KishuCommand.log(notebook_key, basic_execution_ids[-1])
        for commit in log_result.commit_graph:
            assert branch_1 not in commit.branches

    def test_delete_branch_none_existing_branch(
            self, notebook_key, basic_execution_ids):
        delete_result = KishuCommand.delete_branch(notebook_key, "non_existing_branch")
        assert delete_result.status == "error"

    def test_delete_checked_out_branch(
            self, notebook_key, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(notebook_key, branch_1, None)

        delete_result = KishuCommand.delete_branch(notebook_key, branch_1)
        assert delete_result.status == "error"

    def test_rename_branch_basic(self, notebook_key, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(notebook_key, branch_1, None)

        rename_branch_result = KishuCommand.rename_branch(
            notebook_key, branch_1, "new_branch")
        head = KishuBranch.get_head(notebook_key)
        assert rename_branch_result.status == "ok"
        assert head.branch_name == "new_branch"

    def test_rename_branch_non_existing_branch(
            self, notebook_key, basic_execution_ids):
        rename_branch_result = KishuCommand.rename_branch(
            notebook_key, "non_existing_branch", "new_branch")
        assert rename_branch_result.status == "error"

    def test_rename_branch_new_repeating_branch(
            self, notebook_key, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(notebook_key, branch_1, None)

        rename_branch_result = KishuCommand.rename_branch(
            notebook_key, branch_1, branch_1)
        assert rename_branch_result.status == "error"

    def test_auto_detach_commit_branch(self, kishu_jupyter):
        KishuBranch.update_head(kishu_jupyter._notebook_id.key(), branch_name=None, commit_id="0:1", is_detach=True)
        commit = CommitEntry(kind=CommitEntryKind.manual, execution_count=1, code_block="x = 1")
        commit_id = kishu_jupyter.commit(commit)

        head = KishuBranch.get_head(kishu_jupyter._notebook_id.key())
        assert head.branch_name is not None
        assert head.branch_name.startswith("auto_")
        assert head.commit_id == commit_id

    def test_tag(self, notebook_key, basic_execution_ids):
        tag_result = KishuCommand.tag(notebook_key, "at_head", None, "In current time")
        assert tag_result.status == "ok"
        assert tag_result.tag_name == "at_head"
        assert tag_result.commit_id == basic_execution_ids[-1]
        assert tag_result.message == "In current time"

        tag_result = KishuCommand.tag(notebook_key, "historical", basic_execution_ids[1], "")
        assert tag_result.status == "ok"
        assert tag_result.tag_name == "historical"
        assert tag_result.commit_id == basic_execution_ids[1]
        assert tag_result.message == ""

    def test_tag_log(self, notebook_key, basic_execution_ids):
        _ = KishuCommand.tag(notebook_key, "at_head", None, "In current time")
        _ = KishuCommand.tag(notebook_key, "historical", basic_execution_ids[1], "")
        log_result = KishuCommand.log(notebook_key, basic_execution_ids[-1])
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
            branches=["auto_0:1"],
            tags=["at_head"],
        )

    def test_fe_commit_graph(self, notebook_key, basic_execution_ids):
        fe_commit_graph_result = KishuCommand.fe_commit_graph(notebook_key)
        assert len(fe_commit_graph_result.commits) == 3

    def test_fe_commit(self, notebook_key, basic_execution_ids):
        fe_commit_result = KishuCommand.fe_commit(notebook_key, basic_execution_ids[-1], vardepth=0)
        assert fe_commit_result == FESelectedCommit(
            commit=FECommit(
                oid="0:3",
                parent_oid="0:2",
                timestamp=fe_commit_result.commit.timestamp,  # Not tested
                branches=["auto_0:1"],
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

    @pytest.mark.parametrize("notebook_names",
                             [[],
                              ["simple.ipynb"],
                              ["simple.ipynb", "numpy.ipynb"]])
    def test_list_alive_sessions(
        self,
        tmp_kishu_path,
        tmp_kishu_path_os,
        tmp_nb_path,
        jupyter_server,
        notebook_names: List[str],
    ):
        # Start sessions and run kishu init cell in each of these sessions.
        for notebook_name in notebook_names:
            with jupyter_server.start_session(tmp_nb_path(notebook_name)) as notebook_session:
                notebook_session.run_code(KISHU_INIT_STR)

        # Kishu should be able to see these sessions.
        list_result = KishuCommand.list()
        assert len(list_result.sessions) == len(notebook_names)

        # The notebook names reported by Kishu list should match those at the server side.
        kishu_list_notebook_names = [Path(session.notebook_path).name if session.notebook_path is not None
                                     else '' for session in list_result.sessions]
        assert set(notebook_names) == set(kishu_list_notebook_names)

    def test_list_alive_session_no_init(
        self,
        tmp_kishu_path,
        tmp_kishu_path_os,
        tmp_nb_path,
        jupyter_server,
    ):
        # Start the session.
        jupyter_server.start_session(tmp_nb_path("simple.ipynb"))

        # Kishu should not be able to see this session as "kishu init" was not executed.
        list_result = KishuCommand.list()
        assert len(list_result.sessions) == 0

    @pytest.mark.parametrize(
        ("notebook_name", "cell_num_to_restore", "var_to_compare"),
        [
            ('numpy.ipynb', 4, "iris_X_train"),
            ('simple.ipynb', 4, "b")
        ]
    )
    def test_end_to_end_checkout(
        self,
        tmp_kishu_path,
        tmp_kishu_path_os,
        tmp_nb_path,
        jupyter_server,
        notebook_name: str,
        cell_num_to_restore: int,
        var_to_compare: str,
    ):
        # Get the contents of the test notebook.
        notebook_path = tmp_nb_path(notebook_name)
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        assert cell_num_to_restore >= 1 and cell_num_to_restore <= len(contents) - 1

        # Start the notebook session.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR)

            # Run some notebook cells.
            for i in range(cell_num_to_restore):
                notebook_session.run_code(contents[i])

            # Get the variable value before checkout.
            var_value_before = notebook_session.run_code(f"print({var_to_compare})")

            # Run the rest of the notebook cells.
            for i in range(cell_num_to_restore, len(contents)):
                notebook_session.run_code(contents[i])

            # Get the notebook key of the session.
            list_result = KishuCommand.list(list_all=True)
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].notebook_path is not None
            assert Path(list_result.sessions[0].notebook_path).name == notebook_name
            notebook_key = list_result.sessions[0].notebook_key

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log_all(notebook_key)
            assert len(log_result.commit_graph) == len(contents) + 2  # all cells + init cell + print variable cell
            commit_id = log_result.commit_graph[cell_num_to_restore].commit_id

            # Restore to that commit
            KishuCommand.checkout(notebook_key, commit_id)

            # Get the variable value after checkout.
            var_value_after = notebook_session.run_code(f"print({var_to_compare})")
            assert var_value_before == var_value_after
