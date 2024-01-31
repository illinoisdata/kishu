import os
import pytest

from pathlib import Path
from typing import List

from kishu.diff import VariableVersionCompare
from tests.helpers.nbexec import KISHU_INIT_STR

from kishu.commands import (
    CommitSummary,
    DeleteTagResult,
    EditCommitItem,
    FECommit,
    FEFindVarChangeResult,
    FESelectedCommit,
    InstrumentStatus,
    KishuCommand,
    KishuSession,
    TagResult,
)
from kishu.jupyter.runtime import JupyterRuntimeEnv
from kishu.jupyterint import CommitEntryKind, CommitEntry
from kishu.notebook_id import NotebookId
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
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_result.commit_graph[1].runtime_s,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_result.commit_graph[2].branches[0]],  # 1 auto branch
            tags=[],
        )

        log_result = KishuCommand.log(notebook_key, basic_execution_ids[0])
        assert len(log_result.commit_graph) == 1
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
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
            raw_cell="x = 1",
            runtime_s=log_all_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_all_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_all_result.commit_graph[1].message,  # Not tested
            timestamp=log_all_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_all_result.commit_graph[1].runtime_s,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_all_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_all_result.commit_graph[2].message,  # Not tested
            timestamp=log_all_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_all_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_all_result.commit_graph[2].branches[0]],  # 1 auto branch
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
            commit_id="0:3",
            execution_count=3,
            raw_cell="y = x + 1",
            executed_cells=[  # TODO: Missing due to missing IPython kernel.
                "",
                # "x = 1",
                # "y = 2",
                # "y = x + 1",
            ],
            message=status_result.commit_entry.message,  # Not tested,
            timestamp=status_result.commit_entry.timestamp,  # Not tested
            ahg_string=status_result.commit_entry.ahg_string,  # Not tested
            code_version=status_result.commit_entry.code_version,  # Not tested
            varset_version=status_result.commit_entry.varset_version,  # Not tested
            start_time=status_result.commit_entry.start_time,  # Not tested
            end_time=status_result.commit_entry.end_time,  # Not tested
            checkpoint_runtime_s=status_result.commit_entry.checkpoint_runtime_s,  # Not tested
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
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_result.commit_graph[1].runtime_s,  # Not tested
            branches=["historical"],
            tags=[],
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_result.commit_graph[2].branches[0], "at_head"],  # 1 auto branch
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
        head = KishuBranch(notebook_key).get_head()
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
        kishu_branch = KishuBranch(kishu_jupyter._notebook_id.key())
        kishu_branch.update_head(branch_name=None, commit_id="0:1", is_detach=True)
        commit = CommitEntry(kind=CommitEntryKind.manual, execution_count=1, raw_cell="x = 1")
        commit_id = kishu_jupyter.commit(commit)

        head = kishu_branch.get_head()
        assert head.branch_name is not None
        assert "_" in head.branch_name, f"Unexpected branch name {head.branch_name}"
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
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:2",
            parent_id="0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_result.commit_graph[1].runtime_s,  # Not tested
            branches=[],
            tags=["historical"],
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:3",
            parent_id="0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_result.commit_graph[2].branches[0]],  # 1 auto branch
            tags=["at_head"],
        )

    def test_create_tag_specific(self, notebook_key, basic_execution_ids):
        tag_result = KishuCommand.tag(notebook_key, "tag_1", basic_execution_ids[1], "At specific")
        assert tag_result == TagResult(
            status="ok",
            tag_name="tag_1",
            commit_id=basic_execution_ids[1],
            message="At specific",
        )

    def test_tag_list(self, notebook_key, basic_execution_ids):
        _ = KishuCommand.tag(notebook_key, "tag_1", None, "")
        _ = KishuCommand.tag(notebook_key, "tag_2", None, "")
        _ = KishuCommand.tag(notebook_key, "tag_3", None, "")

        list_tag_result = KishuCommand.list_tag(notebook_key)
        assert len(list_tag_result.tags) == 3
        assert set(tag.tag_name for tag in list_tag_result.tags) == {"tag_1", "tag_2", "tag_3"}

    def test_delete_tag(self, notebook_key, basic_execution_ids):
        _ = KishuCommand.tag(notebook_key, "tag_1", None, "")

        delete_tag_result = KishuCommand.delete_tag(notebook_key, "tag_1")
        assert delete_tag_result == DeleteTagResult(
            status="ok",
            message="Tag tag_1 deleted.",
        )

    def test_delete_tag_nonexisting(self, notebook_key, basic_execution_ids):
        _ = KishuCommand.tag(notebook_key, "tag_1", None, "")

        delete_tag_result = KishuCommand.delete_tag(notebook_key, "NON_EXISTENT_TAG")
        assert delete_tag_result == DeleteTagResult(
            status="error",
            message="The provided tag 'NON_EXISTENT_TAG' does not exist.",
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
                branches=[fe_commit_result.commit.branches[0]],  # 1 auto branch
                tags=[],
                code_version=fe_commit_result.commit.code_version,  # Not tested
                varset_version=fe_commit_result.commit.varset_version,  # Not tested
            ),
            executed_cells=[  # TODO: Missing due to missing IPython kernel.
                "",
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
        tmp_nb_path,
        jupyter_server,
        notebook_names: List[str],
    ):
        # Start sessions and run kishu init cell in each of these sessions.
        for notebook_name in notebook_names:
            with jupyter_server.start_session(tmp_nb_path(notebook_name), persist=True) as notebook_session:
                notebook_session.run_code(KISHU_INIT_STR, silent=True)

        # Kishu should be able to see these sessions.
        list_result = KishuCommand.list()
        assert len(list_result.sessions) == len(notebook_names)

        # The notebook names reported by Kishu list should match those at the server side.
        kishu_list_notebook_names = [Path(session.notebook_path).name if session.notebook_path is not None
                                     else '' for session in list_result.sessions]
        assert set(notebook_names) == set(kishu_list_notebook_names)

    def test_list_alive_session_no_init(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        with jupyter_server.start_session(tmp_nb_path("simple.ipynb")):
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
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Run some notebook cells.
            for i in range(cell_num_to_restore):
                notebook_session.run_code(contents[i])

            # Get the variable value before checkout.
            _, var_value_before = notebook_session.run_code(var_to_compare)

            # Run the rest of the notebook cells.
            for i in range(cell_num_to_restore, len(contents)):
                notebook_session.run_code(contents[i])

            # Get the notebook key of the session.
            list_result = KishuCommand.list()
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].notebook_path is not None
            assert Path(list_result.sessions[0].notebook_path).name == notebook_name
            notebook_key = list_result.sessions[0].notebook_key

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log_all(notebook_key)
            assert len(log_result.commit_graph) == len(contents) + 1  # all cells + init cell + print variable cell
            commit_id = log_result.commit_graph[cell_num_to_restore].commit_id

            # Restore to that commit
            KishuCommand.checkout(notebook_path, commit_id)

            # Get the variable value after checkout.
            _, var_value_after = notebook_session.run_code(var_to_compare)
            assert var_value_before == var_value_after

    def test_track_executed_cells_with_checkout(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        # Get the contents of the test notebook.
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        cell_num_to_restore = len(contents) // 2  # Arbitrarily picked one.

        # Start the notebook session.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Run the rest of the notebook cells.
            for i in range(len(contents)):
                notebook_session.run_code(contents[i])

            # Get the notebook key of the session.
            notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path)

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log(notebook_key)
            commit_id = log_result.commit_graph[cell_num_to_restore].commit_id

            # Executed cells should contain all cells from contents.
            status_result = KishuCommand.status(notebook_key, commit_id)
            assert status_result.commit_entry.executed_cells == [
                "",  # PYTHONSTARTUP, https://ipython.readthedocs.io/en/stable/interactive/reference.html
                *contents[:cell_num_to_restore+1],
            ]

            # Restore to that commit
            KishuCommand.checkout(notebook_path, commit_id)

            # Run some cells.
            notebook_session.run_code("x = 1")
            notebook_session.run_code("y = x + 10")

            # Executed cells should work.
            log_result_2 = KishuCommand.log(notebook_key)
            commit_id_2 = log_result_2.commit_graph[-1].commit_id
            status_result_2 = KishuCommand.status(notebook_key, commit_id_2)
            assert status_result_2.commit_entry.executed_cells == [
                "",  # PYTHONSTARTUP, https://ipython.readthedocs.io/en/stable/interactive/reference.html
                *contents[:cell_num_to_restore+1],
                "x = 1",
                "y = x + 10",
            ]

    def test_checkout_reattach(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        cell_num_to_restore = 4
        var_to_compare = "b"

        # Start the initial notebook session.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Run some notebook cells.
            for i in range(cell_num_to_restore):
                notebook_session.run_code(contents[i])

            _, var_value_before = notebook_session.run_code(var_to_compare)

            # Run the rest of the notebook cells.
            for i in range(cell_num_to_restore, len(contents)):
                notebook_session.run_code(contents[i])

            # Get notebook key
            list_result = KishuCommand.list()
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].notebook_path is not None
            assert Path(list_result.sessions[0].notebook_path).name == "simple.ipynb"
            notebook_key = list_result.sessions[0].notebook_key

            # Verifying correct number of entries in commit graph
            log_result = KishuCommand.log_all(notebook_key)
            assert len(log_result.commit_graph) == len(contents)+1  # all contents + init cell
            len_log_result_before = len(log_result.commit_graph)

        # Starting second notebook session
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run all notebook cells, note no init cell ran
            for i in range(len(contents)):
                notebook_session.run_code(contents[i])

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log_all(notebook_key)
            assert len(log_result.commit_graph) == len_log_result_before  # Nothing on this session should have been tracked

            commit_id = log_result.commit_graph[cell_num_to_restore].commit_id

            # Restore to that commit
            checkout_result = KishuCommand.checkout(notebook_path, commit_id)
            assert checkout_result.reattachment.status == InstrumentStatus.reattach_succeeded

            # Get the variable value after checkout.
            _, var_value_after = notebook_session.run_code(var_to_compare)
            assert var_value_before == var_value_after

    def test_commit_checkout_reattach_new_cells(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        var_to_compare = "test_success"
        value_of_var = "1"

        # Start the initial notebook session.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Run some notebook cells.
            for i in range(len(contents)):
                notebook_session.run_code(contents[i])

            # Get notebook key
            list_result = KishuCommand.list()
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].notebook_path is not None
            assert Path(list_result.sessions[0].notebook_path).name == "simple.ipynb"
            notebook_key = list_result.sessions[0].notebook_key

        # Starting second notebook session
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run all notebook cells, note no init cell ran
            notebook_session.run_code(f"{var_to_compare} = {value_of_var}")

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log_all(notebook_key)
            assert len(log_result.commit_graph) == len(contents)  # Nothing on this session should have been tracked

            # Prior to recent fix, this commit is where a KeyError would occur as the variable set changed while untracked
            commit_result = KishuCommand.commit(notebook_path, "Reattatch_commit")
            assert commit_result.reattachment.status == InstrumentStatus.reattach_succeeded

            log_result = KishuCommand.log_all(notebook_key)
            assert len(log_result.commit_graph) == len(contents)+1  # Addition of the new cell

            commit_id = log_result.commit_graph[-1].commit_id

            # Restore to the commit (testing if the commit included the new cell)
            checkout_result = KishuCommand.checkout(notebook_path, commit_id)
            assert checkout_result.reattachment.status == InstrumentStatus.already_attached

            # Get the variable value after checkout.
            _, var_value_after = notebook_session.run_code(var_to_compare)
            assert var_value_after == value_of_var

    def test_edit_commit_by_commit_id(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        notebook_path = tmp_nb_path("simple.ipynb")

        # Start a notebook session.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Create a commit
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path)
            commit_result = KishuCommand.commit(notebook_path, "Wrong message")
            assert commit_result.status == "ok"

            # Get most recent commit ID.
            log_result = KishuCommand.log_all(notebook_key)
            commit_id = log_result.commit_graph[-1].commit_id

            # Edit the commit.
            edit_result = KishuCommand.edit_commit(
                notebook_path,
                commit_id,
                message="Correct one",
            )
            assert edit_result.status == "ok"
            assert edit_result.edited == [
                EditCommitItem(field="message", before="Wrong message", after="Correct one"),
            ]

            # Assert commit in database
            status_result = KishuCommand.status(notebook_key, commit_id)
            assert status_result.commit_entry.message == "Correct one"

    def test_edit_commit_by_branch_name(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        notebook_path = tmp_nb_path("simple.ipynb")

        # Start a notebook session.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Create a commit
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path)
            commit_result = KishuCommand.commit(notebook_path, "Wrong message")
            assert commit_result.status == "ok"

            # Get most recent commit ID.
            log_result = KishuCommand.log_all(notebook_key)
            commit_id = log_result.commit_graph[-1].commit_id

            # Create a branch at current commit.
            branch_result = KishuCommand.branch(notebook_key, "stick", None)
            assert branch_result.status == "ok"
            assert branch_result.branch_name == "stick"
            assert branch_result.commit_id == commit_id

            # Edit the commit.
            edit_result = KishuCommand.edit_commit(
                notebook_path,
                commit_id,
                message="Correct one",
            )
            assert edit_result.status == "ok"
            assert edit_result.edited == [
                EditCommitItem(field="message", before="Wrong message", after="Correct one"),
            ]

            # Assert commit in database
            status_result = KishuCommand.status(notebook_key, commit_id)
            assert status_result.commit_entry.message == "Correct one"

    def test_edit_commit_by_commit_id_not_exist(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        notebook_path = tmp_nb_path("simple.ipynb")

        # Start a notebook session.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Create a commit
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            commit_result = KishuCommand.commit(notebook_path, "Wrong message")
            assert commit_result.status == "ok"

            # Edit the commit.
            edit_result = KishuCommand.edit_commit(
                notebook_path,
                "this_commit_message_does_not_exist",
                message="Correct one",
            )
            assert edit_result.status == "error"
            assert edit_result.edited == []

    def test_init_in_nonempty_session(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        # Start the notebook session. Even though this test doesn't use the notebook contents, the session
        # still must be based on an existing notebook file.
        with jupyter_server.start_session(tmp_nb_path("simple.ipynb")) as notebook_session:
            # Kishu should not be able to see this session as "kishu init" has not yet been executed.
            list_result = KishuCommand.list()
            assert len(list_result.sessions) == 0

            # Run some notebook cells.
            notebook_session.run_code("x = 1")
            notebook_session.run_code("x += 1")

            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Kishu should be able to see the notebook session now.
            list_result = KishuCommand.list()
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].notebook_path is not None
            assert Path(list_result.sessions[0].notebook_path).name == "simple.ipynb"

            # Run one more cell.
            _, x_value = notebook_session.run_code("x")
            assert x_value == "2"

    def test_variable_diff(self, jupyter_server, tmp_nb_path):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            for content in contents[0:2]:
                notebook_session.run_code(content)

            # Get notebook key
            list_result = KishuCommand.list()
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].notebook_path is not None
            assert Path(list_result.sessions[0].notebook_path).name == "simple.ipynb"
            notebook_key = list_result.sessions[0].notebook_key

            # get the commit ids
            commits = KishuCommand.log_all(notebook_key).commit_graph
            source_commit_id = commits[0].commit_id
            dest_commit_id = commits[-1].commit_id

            diff_result = KishuCommand.variable_diff(notebook_key, source_commit_id, dest_commit_id)
            assert set(diff_result) == {VariableVersionCompare('a', 'destination_only'),
                                        VariableVersionCompare('z', 'destination_only'),
                                        VariableVersionCompare('y', 'destination_only'),
                                        VariableVersionCompare('x', 'both_different_version')}

    def test_variable_filter(self, jupyter_server, tmp_nb_path):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            for content in contents:
                notebook_session.run_code(content)

            # Get notebook key
            list_result = KishuCommand.list()
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].notebook_path is not None
            assert Path(list_result.sessions[0].notebook_path).name == "simple.ipynb"
            notebook_key = list_result.sessions[0].notebook_key

            commits = KishuCommand.log_all(notebook_key).commit_graph

            diff_result = KishuCommand.find_var_change(notebook_key, 'b')
            assert diff_result == FEFindVarChangeResult([commits[3].commit_id, commits[4].commit_id])
            diff_result = KishuCommand.find_var_change(notebook_key, 'y')
            assert diff_result == FEFindVarChangeResult([commits[1].commit_id])
