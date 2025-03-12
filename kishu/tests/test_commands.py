from pathlib import Path
from typing import Generator, List

import pytest

from kishu.commands import (
    CommitFilter,
    CommitSummary,
    DeleteTagResult,
    EditCommitItem,
    FECommit,
    FEFindVarChangeResult,
    FESelectedCommit,
    InstrumentStatus,
    KishuCommand,
    TagResult,
)
from kishu.diff import CodeDiffHunk, VariableVersionCompare
from kishu.jupyter.runtime import JupyterRuntimeEnv
from kishu.jupyterint import CommitEntry, CommitEntryKind, NotebookCommitState
from kishu.storage.branch import KishuBranch
from kishu.storage.commit_graph import ABSOLUTE_PAST, CommitNodeInfo, KishuCommitGraph
from kishu.storage.config import Config
from kishu.storage.path import KishuPath
from tests.helpers.nbexec import KISHU_INIT_STR


@pytest.fixture()
def disable_always_migrate(tmp_kishu_path) -> Generator[type, None, None]:
    prev_value = Config.get("OPTIMIZER", "always_migrate", True)
    Config.set("OPTIMIZER", "always_migrate", False)
    yield Config
    Config.set("OPTIMIZER", "always_migrate", prev_value)


class TestKishuCommand:

    def test_list_noalive(self, set_notebook_path_env, notebook_key, basic_execution_ids):
        list_result = KishuCommand.list()
        assert len(list_result.sessions) == 0

        # TODO: Test list_all with non-alive sessions.
        # list_result = KishuCommand.list(list_all=True)
        # assert len(list_result.sessions) == 1
        # assert list_result.sessions[0] == KishuSession(
        #     notebook_key=notebook_key,
        #     kernel_id="test_kernel_id",
        #     notebook_path=os.environ.get("TEST_NOTEBOOK_PATH"),
        #     is_alive=False,
        # )

    def test_log(self, basic_notebook_path, basic_execution_ids):
        log_result = KishuCommand.log(basic_notebook_path, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
            kind="jupyter",
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:0:2",
            parent_id="0:0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_result.commit_graph[1].runtime_s,  # Not tested
            branches=[],
            tags=[],
            kind="jupyter",
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:0:3",
            parent_id="0:0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_result.commit_graph[2].branches[0]],  # 1 auto branch
            tags=[],
            kind="jupyter",
        )

        log_result = KishuCommand.log(basic_notebook_path, basic_execution_ids[0])
        assert len(log_result.commit_graph) == 1
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
            kind="jupyter",
        )

    def test_log_filter(self, basic_notebook_path, basic_execution_ids):
        assert (
            len(
                KishuCommand.log(
                    basic_notebook_path, basic_execution_ids[-1], commit_filter=CommitFilter(kinds=["jupyter"])
                ).commit_graph
            )
            == 3
        )
        assert (
            len(
                KishuCommand.log(
                    basic_notebook_path, basic_execution_ids[-1], commit_filter=CommitFilter(kinds=["manual"])
                ).commit_graph
            )
            == 0
        )
        assert (
            len(
                KishuCommand.log(
                    basic_notebook_path, basic_execution_ids[-1], commit_filter=CommitFilter(kinds=["jupyter", "manual"])
                ).commit_graph
            )
            == 3
        )

    def test_log_all(self, basic_notebook_path, basic_execution_ids):
        log_all_result = KishuCommand.log_all(basic_notebook_path)
        assert len(log_all_result.commit_graph) == 3
        assert log_all_result.commit_graph[0] == CommitSummary(
            commit_id="0:0:1",
            parent_id="",
            message=log_all_result.commit_graph[0].message,  # Not tested
            timestamp=log_all_result.commit_graph[0].timestamp,  # Not tested
            raw_cell="x = 1",
            runtime_s=log_all_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
            kind="jupyter",
        )
        assert log_all_result.commit_graph[1] == CommitSummary(
            commit_id="0:0:2",
            parent_id="0:0:1",
            message=log_all_result.commit_graph[1].message,  # Not tested
            timestamp=log_all_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_all_result.commit_graph[1].runtime_s,  # Not tested
            branches=[],
            tags=[],
            kind="jupyter",
        )
        assert log_all_result.commit_graph[2] == CommitSummary(
            commit_id="0:0:3",
            parent_id="0:0:2",
            message=log_all_result.commit_graph[2].message,  # Not tested
            timestamp=log_all_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_all_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_all_result.commit_graph[2].branches[0]],  # 1 auto branch
            tags=[],
            kind="jupyter",
        )

    def test_status(self, basic_notebook_path, basic_execution_ids):
        status_result = KishuCommand.status(basic_notebook_path, basic_execution_ids[-1])
        assert status_result.commit_node_info == CommitNodeInfo(
            commit_id="0:0:3",
            parent_id="0:0:2",
        )
        assert status_result.commit_entry == CommitEntry(
            kind=CommitEntryKind.jupyter,
            commit_id="0:0:3",
            execution_count=3,
            raw_cell="y = x + 1",
            executed_cells=[  # TODO: Missing due to missing IPython kernel.
                "",
                # "x = 1",
                # "y = 2",
                # "y = x + 1",
            ],
            executed_outputs={},
            nb_record_type=NotebookCommitState.with_commit,
            message=status_result.commit_entry.message,  # Not tested,
            timestamp=status_result.commit_entry.timestamp,  # Not tested
            code_version=status_result.commit_entry.code_version,  # Not tested
            varset_version=status_result.commit_entry.varset_version,  # Not tested
            start_time=status_result.commit_entry.start_time,  # Not tested
            end_time=status_result.commit_entry.end_time,  # Not tested
            checkpoint_runtime_s=status_result.commit_entry.checkpoint_runtime_s,  # Not tested
            raw_nb=status_result.commit_entry.raw_nb,  # Not tested
            formatted_cells=status_result.commit_entry.formatted_cells,  # Not tested
            restore_plan=status_result.commit_entry.restore_plan,  # Not tested
        )

    def test_branch(self, basic_notebook_path, basic_execution_ids):
        branch_result = KishuCommand.branch(basic_notebook_path, "at_head", None)
        assert branch_result.status == "ok"

        branch_result = KishuCommand.branch(basic_notebook_path, "historical", basic_execution_ids[1])
        assert branch_result.status == "ok"

    def test_branch_log(self, basic_notebook_path, basic_execution_ids):
        _ = KishuCommand.branch(basic_notebook_path, "at_head", None)
        _ = KishuCommand.branch(basic_notebook_path, "historical", basic_execution_ids[1])
        log_result = KishuCommand.log(basic_notebook_path, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id="0:0:1",
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
            kind="jupyter",
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id="0:0:2",
            parent_id="0:0:1",
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_result.commit_graph[1].runtime_s,  # Not tested
            branches=["historical"],
            tags=[],
            kind="jupyter",
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id="0:0:3",
            parent_id="0:0:2",
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_result.commit_graph[2].branches[0], "at_head"],  # 1 auto branch
            tags=[],
            kind="jupyter",
        )

    def test_delete_basic(self, basic_notebook_path, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(basic_notebook_path, branch_1, basic_execution_ids[1])

        delete_result = KishuCommand.delete_branch(basic_notebook_path, branch_1)
        assert delete_result.status == "ok"

        log_result = KishuCommand.log(basic_notebook_path, basic_execution_ids[-1])
        for commit in log_result.commit_graph:
            assert branch_1 not in commit.branches

    def test_delete_branch_none_existing_branch(self, basic_notebook_path, basic_execution_ids):
        delete_result = KishuCommand.delete_branch(basic_notebook_path, "non_existing_branch")
        assert delete_result.status == "error"

    def test_delete_checked_out_branch(self, basic_notebook_path, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(basic_notebook_path, branch_1, None)

        delete_result = KishuCommand.delete_branch(basic_notebook_path, branch_1)
        assert delete_result.status == "error"

    def test_rename_branch_basic(self, basic_notebook_path, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(basic_notebook_path, branch_1, None)

        rename_branch_result = KishuCommand.rename_branch(basic_notebook_path, branch_1, "new_branch")
        head = KishuBranch(KishuPath.database_path(basic_notebook_path)).get_head()
        assert rename_branch_result.status == "ok"
        assert head.branch_name == "new_branch"

    def test_rename_branch_non_existing_branch(self, basic_notebook_path, basic_execution_ids):
        rename_branch_result = KishuCommand.rename_branch(basic_notebook_path, "non_existing_branch", "new_branch")
        assert rename_branch_result.status == "error"

    def test_rename_branch_new_repeating_branch(self, basic_notebook_path, basic_execution_ids):
        branch_1 = "branch_1"
        KishuCommand.branch(basic_notebook_path, branch_1, None)

        rename_branch_result = KishuCommand.rename_branch(basic_notebook_path, branch_1, branch_1)
        assert rename_branch_result.status == "error"

    def test_auto_detach_commit_branch(self, kishu_jupyter, basic_notebook_path):
        kishu_branch = KishuBranch(KishuPath.database_path(basic_notebook_path))
        kishu_branch.update_head(branch_name=None, commit_id="0:0:1", is_detach=True)
        commit = CommitEntry(kind=CommitEntryKind.manual, execution_count=1, raw_cell="x = 1")
        commit_id = kishu_jupyter.commit(commit)

        head = kishu_branch.get_head()
        assert head.branch_name is not None
        assert "_" in head.branch_name, f"Unexpected branch name {head.branch_name}"
        assert head.commit_id == commit_id

    def test_tag(self, basic_notebook_path, basic_execution_ids):
        tag_result = KishuCommand.tag(basic_notebook_path, "at_head", None, "In current time")
        assert tag_result.status == "ok"
        assert tag_result.tag_name == "at_head"
        assert tag_result.commit_id == basic_execution_ids[-1]
        assert tag_result.message == "In current time"

        tag_result = KishuCommand.tag(basic_notebook_path, "historical", basic_execution_ids[1], "")
        assert tag_result.status == "ok"
        assert tag_result.tag_name == "historical"
        assert tag_result.commit_id == basic_execution_ids[1]
        assert tag_result.message == ""

    def test_tag_log(self, basic_notebook_path, basic_execution_ids):
        _ = KishuCommand.tag(basic_notebook_path, "at_head", None, "In current time")
        _ = KishuCommand.tag(basic_notebook_path, "historical", basic_execution_ids[1], "")
        log_result = KishuCommand.log(basic_notebook_path, basic_execution_ids[-1])
        assert len(log_result.commit_graph) == 3
        assert log_result.commit_graph[0] == CommitSummary(
            commit_id=basic_execution_ids[0],
            parent_id="",
            message=log_result.commit_graph[0].message,  # Not tested
            timestamp=log_result.commit_graph[0].timestamp,  # Not tested
            raw_cell="x = 1",
            runtime_s=log_result.commit_graph[0].runtime_s,  # Not tested
            branches=[],
            tags=[],
            kind="jupyter",
        )
        assert log_result.commit_graph[1] == CommitSummary(
            commit_id=basic_execution_ids[1],
            parent_id=basic_execution_ids[0],
            message=log_result.commit_graph[1].message,  # Not tested
            timestamp=log_result.commit_graph[1].timestamp,  # Not tested
            raw_cell="y = 2",
            runtime_s=log_result.commit_graph[1].runtime_s,  # Not tested
            branches=[],
            tags=["historical"],
            kind="jupyter",
        )
        assert log_result.commit_graph[2] == CommitSummary(
            commit_id=basic_execution_ids[2],
            parent_id=basic_execution_ids[1],
            message=log_result.commit_graph[2].message,  # Not tested
            timestamp=log_result.commit_graph[2].timestamp,  # Not tested
            raw_cell="y = x + 1",
            runtime_s=log_result.commit_graph[2].runtime_s,  # Not tested
            branches=[log_result.commit_graph[2].branches[0]],  # 1 auto branch
            tags=["at_head"],
            kind="jupyter",
        )

    def test_create_tag_specific(self, basic_notebook_path, basic_execution_ids):
        tag_result = KishuCommand.tag(basic_notebook_path, "tag_1", basic_execution_ids[1], "At specific")
        assert tag_result == TagResult(
            status="ok",
            tag_name="tag_1",
            commit_id=basic_execution_ids[1],
            message="At specific",
        )

    def test_tag_list(self, basic_notebook_path, basic_execution_ids):
        _ = KishuCommand.tag(basic_notebook_path, "tag_1", None, "")
        _ = KishuCommand.tag(basic_notebook_path, "tag_2", None, "")
        _ = KishuCommand.tag(basic_notebook_path, "tag_3", None, "")

        list_tag_result = KishuCommand.list_tag(basic_notebook_path)
        assert len(list_tag_result.tags) == 3
        assert set(tag.tag_name for tag in list_tag_result.tags) == {"tag_1", "tag_2", "tag_3"}

    def test_delete_tag(self, basic_notebook_path, basic_execution_ids):
        _ = KishuCommand.tag(basic_notebook_path, "tag_1", None, "")

        delete_tag_result = KishuCommand.delete_tag(basic_notebook_path, "tag_1")
        assert delete_tag_result == DeleteTagResult(
            status="ok",
            message="Tag tag_1 deleted.",
        )

    def test_delete_tag_nonexisting(self, basic_notebook_path, basic_execution_ids):
        _ = KishuCommand.tag(basic_notebook_path, "tag_1", None, "")

        delete_tag_result = KishuCommand.delete_tag(basic_notebook_path, "NON_EXISTENT_TAG")
        assert delete_tag_result == DeleteTagResult(
            status="error",
            message="The provided tag 'NON_EXISTENT_TAG' does not exist.",
        )

    def test_fe_commit_graph(self, basic_notebook_path, basic_execution_ids):
        fe_commit_graph_result = KishuCommand.fe_commit_graph(basic_notebook_path)
        assert len(fe_commit_graph_result.commits) == 3

    def test_fe_commit(self, basic_notebook_path, basic_execution_ids):
        fe_commit_result = KishuCommand.fe_commit(basic_notebook_path, basic_execution_ids[-1], vardepth=0)
        assert fe_commit_result == FESelectedCommit(
            commit=FECommit(
                oid=basic_execution_ids[-1],
                parent_oid=basic_execution_ids[-2],
                nb_parent_oid=basic_execution_ids[-2],
                timestamp=fe_commit_result.commit.timestamp,  # Not tested
                branches=[fe_commit_result.commit.branches[0]],  # 1 auto branch
                tags=[],
                code_version=fe_commit_result.commit.code_version,  # Not tested
                varset_version=fe_commit_result.commit.varset_version,  # Not tested
                message="[3] y = x + 1",
            ),
            executed_cells=[  # TODO: Missing due to missing IPython kernel.
                "",
                # "x = 1",
                # "y = 2",
                # "y = x + 1",
            ],
            executed_outputs={},
            cells=fe_commit_result.cells,  # Not tested
            variables=[],
        )

    @pytest.mark.parametrize("notebook_names", [[], ["simple.ipynb"], ["simple.ipynb", "numpy.ipynb"]])
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
        kishu_list_notebook_names = [
            Path(session.notebook_path).name if session.notebook_path is not None else "" for session in list_result.sessions
        ]
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

    def _test_end_to_end_checkout(
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
            # The variable is printed so custom objects with no equality defined can be compared.
            _, var_value_before = notebook_session.run_code(f"repr({var_to_compare})")

            # Run the rest of the notebook cells.
            for i in range(cell_num_to_restore, len(contents)):
                notebook_session.run_code(contents[i])

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log_all(notebook_path)
            assert len(log_result.commit_graph) == len(contents) + 1  # all cells + init cell + print variable cell
            commit_id = log_result.commit_graph[cell_num_to_restore - 1].commit_id  # Want to checkout to cell before printing

            # Restore to that commit
            KishuCommand.checkout(notebook_path, commit_id)

            # Get the variable value after checkout.
            _, var_value_after = notebook_session.run_code(f"repr({var_to_compare})")
            assert var_value_before == var_value_after

    @pytest.mark.parametrize(
        ("notebook_name", "cell_num_to_restore", "var_to_compare"),
        [
            ("numpy.ipynb", 4, "iris_X_train"),
            ("simple.ipynb", 4, "b"),
            ("test_unserializable_var.ipynb", 2, "next(gen)"),  # directly printing gen prints out its memory address.
            pytest.param("QiskitDemo_NCSA_May2023.ipynb", 61, "qc", marks=pytest.mark.skip(reason="Flaky")),
        ],
    )
    def test_end_to_end_checkout(
        self,
        tmp_nb_path,
        disable_incremental_store,
        disable_always_migrate,
        jupyter_server,
        notebook_name: str,
        cell_num_to_restore: int,
        var_to_compare: str,
    ):
        self._test_end_to_end_checkout(
            tmp_nb_path,
            jupyter_server,
            notebook_name,
            cell_num_to_restore,
            var_to_compare,
        )

    @pytest.mark.parametrize(
        ("notebook_name", "cell_num_to_restore", "var_to_compare"),
        [
            ("numpy.ipynb", 4, "iris_X_train"),
            ("simple.ipynb", 4, "b"),
            ("test_unserializable_var.ipynb", 2, "next(gen)"),
            pytest.param("QiskitDemo_NCSA_May2023.ipynb", 61, "qc", marks=pytest.mark.skip(reason="Flaky")),
        ],
    )
    def test_incremental_end_to_end_checkout(
        self,
        tmp_nb_path,
        enable_incremental_store,
        jupyter_server,
        notebook_name: str,
        cell_num_to_restore: int,
        var_to_compare: str,
    ):
        assert Config.get("PLANNER", "incremental_store", False)
        self._test_end_to_end_checkout(
            tmp_nb_path,
            jupyter_server,
            notebook_name,
            cell_num_to_restore,
            var_to_compare,
        )

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

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log(notebook_path)
            commit_id = log_result.commit_graph[cell_num_to_restore].commit_id

            # Executed cells should contain all cells from contents.
            status_result = KishuCommand.status(notebook_path, commit_id)
            assert status_result.commit_entry.executed_cells == [
                "",  # PYTHONSTARTUP, https://ipython.readthedocs.io/en/stable/interactive/reference.html
                *contents[: cell_num_to_restore + 1],
            ]
            assert status_result.commit_entry.execution_count == (cell_num_to_restore + 1)

            # Restore to that commit
            KishuCommand.checkout(notebook_path, commit_id)

            # Run some cells.
            notebook_session.run_code("x = 1")
            notebook_session.run_code("y = x + 10")

            # Executed cells should work.
            log_result_2 = KishuCommand.log(notebook_path)
            commit_id_2 = log_result_2.commit_graph[-1].commit_id
            status_result_2 = KishuCommand.status(notebook_path, commit_id_2)
            assert status_result_2.commit_entry.executed_cells == [
                "",  # PYTHONSTARTUP, https://ipython.readthedocs.io/en/stable/interactive/reference.html
                *contents[: cell_num_to_restore + 1],
                "x = 1",
                "y = x + 10",
            ]
            assert status_result_2.commit_entry.execution_count == (cell_num_to_restore + 1) + 2

    def test_fe_commit_after_rollback_execution(
        self,
        tmp_nb_path,
        disable_incremental_store,
        disable_always_migrate,
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

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log(notebook_path)
            commit_id = log_result.commit_graph[cell_num_to_restore].commit_id
            parent_commit_id = log_result.commit_graph[cell_num_to_restore - 1].commit_id
            latest_commit_id = log_result.commit_graph[-1].commit_id
            fe_commit_result = KishuCommand.fe_commit(notebook_path, commit_id, vardepth=0)
            assert fe_commit_result == FESelectedCommit(
                commit=FECommit(
                    oid=commit_id,
                    parent_oid=parent_commit_id,
                    nb_parent_oid=parent_commit_id,
                    timestamp=fe_commit_result.commit.timestamp,  # Not tested
                    branches=[],
                    tags=[],
                    code_version=fe_commit_result.commit.code_version,  # Not tested
                    varset_version=fe_commit_result.commit.varset_version,  # Not tested
                    message="[4] b = 1",
                ),
                executed_cells=[  # TODO: Missing due to missing IPython kernel.
                    "",
                    "x = 1",
                    "y = x\nx = x + 1\nz = 1\na = 1\ndel a\na = 2",
                    "# Record imported libraries\nimport numpy as np\nfrom numpy import random",
                    "b = 1",
                ],
                executed_outputs={},
                cells=fe_commit_result.cells,  # Not tested
                variables=fe_commit_result.variables,  # Not tested
            )

            # Rollback execution to that commit.
            KishuCommand.checkout(notebook_path, commit_id, skip_notebook=True)

            # Run a cell. This commit should have different state and notebook parents.
            notebook_session.run_code("x = 1")

            # Executed cells should work.
            log_result_2 = KishuCommand.log(notebook_path)
            commit_id_2 = log_result_2.commit_graph[-1].commit_id
            fe_commit_result_2 = KishuCommand.fe_commit(notebook_path, commit_id_2, vardepth=0)
            assert fe_commit_result_2 == FESelectedCommit(
                commit=FECommit(
                    oid=commit_id_2,
                    parent_oid=commit_id,
                    nb_parent_oid=latest_commit_id,
                    timestamp=fe_commit_result_2.commit.timestamp,  # Not tested
                    branches=[fe_commit_result_2.commit.branches[0]],  # 1 auto branch
                    tags=[],
                    code_version=fe_commit_result_2.commit.code_version,  # Not tested
                    varset_version=fe_commit_result_2.commit.varset_version,  # Not tested
                    message="[5] x = 1",
                ),
                executed_cells=[  # TODO: Missing due to missing IPython kernel.
                    "",
                    "x = 1",
                    "y = x\nx = x + 1\nz = 1\na = 1\ndel a\na = 2",
                    "# Record imported libraries\nimport numpy as np\nfrom numpy import random",
                    "b = 1",
                    "x = 1",
                ],
                executed_outputs={},
                cells=fe_commit_result_2.cells,  # Not tested
                variables=fe_commit_result_2.variables,  # Not tested
            )

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

            # Verifying correct number of entries in commit graph
            log_result = KishuCommand.log_all(notebook_path)
            assert len(log_result.commit_graph) == len(contents) + 1  # all contents + init cell
            len_log_result_before = len(log_result.commit_graph)

        # Starting second notebook session
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run all notebook cells, note no init cell ran
            for i in range(len(contents)):
                notebook_session.run_code(contents[i])

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log_all(notebook_path)
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

        # Starting second notebook session
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run all notebook cells, note no init cell ran
            notebook_session.run_code(f"{var_to_compare} = {value_of_var}")

            # Get commit id of commit which we want to restore
            log_result = KishuCommand.log_all(notebook_path)

            assert len(log_result.commit_graph) == len(contents)  # Nothing on this session should have been tracked

            # Prior to recent fix, this commit is where a KeyError would occur as the variable set changed while untracked
            commit_result = KishuCommand.commit(notebook_path, "Reattatch_commit")
            assert commit_result.reattachment.status == InstrumentStatus.reattach_succeeded

            log_result = KishuCommand.log_all(notebook_path)
            assert len(log_result.commit_graph) == len(contents) + 1  # Addition of the new cell

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
            commit_result = KishuCommand.commit(notebook_path, "Wrong message")
            assert commit_result.status == "ok"

            # Get most recent commit ID.
            log_result = KishuCommand.log_all(notebook_path)
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
            status_result = KishuCommand.status(notebook_path, commit_id)
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
            commit_result = KishuCommand.commit(notebook_path, "Wrong message")
            assert commit_result.status == "ok"

            # Get most recent commit ID.
            log_result = KishuCommand.log_all(notebook_path)
            commit_id = log_result.commit_graph[-1].commit_id

            # Create a branch at current commit.
            branch_result = KishuCommand.branch(notebook_path, "stick", None)
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
            status_result = KishuCommand.status(notebook_path, commit_id)
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

    def test_init_reattachment(
        self,
        tmp_nb_path,
        jupyter_server,
    ):
        # Start the notebook session. Even though this test doesn't use the notebook contents, the session
        # still must be based on an existing notebook file.
        notebook_path = tmp_nb_path("simple.ipynb")
        database_path = KishuPath.database_path(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Run some notebook cells.
            notebook_session.run_code("x = 1")
            notebook_session.run_code("x += 1")

            # Check head state.
            assert KishuCommand.log(notebook_path).head.commit_id is not None
            assert KishuCommitGraph.new_var_graph(database_path).head() is not None
            assert KishuCommitGraph.new_nb_graph(database_path).head() is not None

        # Test reattachment state.
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell to reattach.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Check head state.
            assert KishuCommand.log(notebook_path).head.commit_id is None
            assert KishuCommitGraph.new_var_graph(database_path).head() is ABSOLUTE_PAST
            assert KishuCommitGraph.new_nb_graph(database_path).head() is ABSOLUTE_PAST

    def test_variable_diff(self, jupyter_server, tmp_nb_path):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            for content in contents[0:2]:
                notebook_session.run_code(content)

            # get the commit ids
            commits = KishuCommand.log_all(notebook_path).commit_graph
            source_commit_id = commits[0].commit_id
            dest_commit_id = commits[-1].commit_id

            diff_result = KishuCommand.variable_diff(notebook_path, source_commit_id, dest_commit_id)
            assert set(diff_result) == {
                VariableVersionCompare("a", "destination_only"),
                VariableVersionCompare("z", "destination_only"),
                VariableVersionCompare("y", "destination_only"),
                VariableVersionCompare("x", "both_different_version"),
            }

    def test_fe_code_diff(self, jupyter_server, tmp_nb_path):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            for content in contents[0:2]:
                notebook_session.run_code(content)

            # get the commit ids
            commits = KishuCommand.log_all(notebook_path).commit_graph
            source_commit_id = commits[0].commit_id
            dest_commit_id = commits[-1].commit_id

            diff_result = KishuCommand.fe_code_diff(notebook_path, source_commit_id, dest_commit_id)

            assert diff_result.executed_cells_diff == [
                CodeDiffHunk(option="Both", content="", sub_diff_hunks=None),
                CodeDiffHunk(option="Both", content="x = 1", sub_diff_hunks=None),
                CodeDiffHunk(
                    option="Destination_only", content="y = x\nx = x + 1\nz = 1\na = 1\ndel a\na = 2", sub_diff_hunks=None
                ),
            ]

            assert diff_result.notebook_cells_diff == [
                CodeDiffHunk(option="Both", content="x = 1", sub_diff_hunks=None),
                CodeDiffHunk(option="Both", content="y = x\nx = x + 1\nz = 1\na = 1\ndel a\na = 2", sub_diff_hunks=None),
                CodeDiffHunk(
                    option="Both",
                    content="# Record imported libraries\nimport numpy as np\nfrom numpy import random",
                    sub_diff_hunks=None,
                ),
                CodeDiffHunk(option="Both", content="b = 1", sub_diff_hunks=None),
                CodeDiffHunk(option="Both", content="def func():\n    global b\n    b += 1\nfunc()", sub_diff_hunks=None),
                CodeDiffHunk(option="Both", content="del a", sub_diff_hunks=None),
            ]

    def test_variable_filter(self, jupyter_server, tmp_nb_path):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            for content in contents:
                notebook_session.run_code(content)

            commits = KishuCommand.log_all(notebook_path).commit_graph

            diff_result = KishuCommand.find_var_change(notebook_path, "b")
            assert diff_result == FEFindVarChangeResult([commits[3].commit_id, commits[4].commit_id])
            diff_result = KishuCommand.find_var_change(notebook_path, "y")
            assert diff_result == FEFindVarChangeResult([commits[1].commit_id])
            diff_result = KishuCommand.find_var_change(notebook_path, "a")
            assert diff_result == FEFindVarChangeResult([commits[1].commit_id, commits[5].commit_id])

    def test_undo(self, jupyter_server, tmp_nb_path):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # This runs two cells. When undoing, they will be undone one by one.
            for content in contents[0:2]:
                notebook_session.run_code(content)

            commits = KishuCommand.log_all(notebook_path).commit_graph

            # Undo and assert the head id after undo is correct.
            undoResult = KishuCommand.undo(notebook_path)
            assert undoResult.status == "ok"
            head = KishuBranch(KishuPath.database_path(notebook_path)).get_head()
            assert head.commit_id == commits[0].commit_id

            # Undo when current node is root.
            undoResult = KishuCommand.undo(notebook_path)
            assert undoResult.status == "ok"
            assert undoResult.message == "No more commits to undo"

    def test_undo_skip_manual(self, jupyter_server, tmp_nb_path):
        notebook_path = tmp_nb_path("simple.ipynb")
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # This runs two cells and make manual commits each time.
            for idx, content in enumerate(contents[0:2]):
                notebook_session.run_code(content)
                manual_commit = KishuCommand.commit(notebook_path, f"Manual after cell {idx}")
                assert manual_commit.status == "ok"

            commits = KishuCommand.log_all(notebook_path).commit_graph

            # Undo and assert the head id after undo is correct.
            undoResult = KishuCommand.undo(notebook_path)
            assert undoResult.status == "ok"
            head = KishuBranch(KishuPath.database_path(notebook_path)).get_head()
            assert head.commit_id == commits[0].commit_id

            # Undo when current node is root.
            undoResult = KishuCommand.undo(notebook_path)
            assert undoResult.status == "ok"
            assert undoResult.message == "No more commits to undo"
