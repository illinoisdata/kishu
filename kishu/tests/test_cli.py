from typing import Generator, List

import pytest
from typer.testing import CliRunner

from kishu import __app_name__, __version__
from kishu.cli import kishu_app, kishu_experimental_app
from kishu.exceptions import KishuNotInitializedError, NotebookNotFoundError, PathIsNotNotebookError
from kishu.jupyter.runtime import JupyterRuntimeEnv
from tests.helpers.nbexec import KISHU_INIT_STR


@pytest.fixture()
def runner() -> Generator[CliRunner, None, None]:
    yield CliRunner(mix_stderr=False)


class TestKishuApp:

    def test_version(self, runner):
        result = runner.invoke(kishu_app, ["--version"])
        assert result.exit_code == 0
        assert f"{__app_name__} v{__version__}\n" in result.stdout

    def test_v(self, runner):
        result = runner.invoke(kishu_app, ["-v"])
        assert result.exit_code == 0
        assert f"{__app_name__} v{__version__}\n" in result.stdout

    def test_list_empty(self, runner):
        result = runner.invoke(kishu_app, ["list"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "ListResult(sessions=[])"

        result = runner.invoke(kishu_app, ["list", "-a"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "ListResult(sessions=[])"

        result = runner.invoke(kishu_app, ["list", "--all"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "ListResult(sessions=[])"

    def test_init_empty(self, runner):
        result = runner.invoke(kishu_app, ["init", "non_existent_notebook.ipynb"])
        assert result.exit_code == 1
        assert isinstance(result.exception, NotebookNotFoundError)

    def test_detach_empty(self, runner):
        result = runner.invoke(kishu_app, ["detach", "non_existent_notebook.ipynb"])
        assert result.exit_code == 1
        assert isinstance(result.exception, NotebookNotFoundError)

    def test_detach_simple(self, runner, nb_simple_path, jupyter_server):
        with jupyter_server.start_session(nb_simple_path):
            init_result_raw = runner.invoke(kishu_app, ["init", str(nb_simple_path)])
            assert init_result_raw.exit_code == 0
            detach_result_raw = runner.invoke(kishu_app, ["detach", str(nb_simple_path)])
            assert detach_result_raw.exit_code == 0
            assert "Successfully detached notebook at " in detach_result_raw.stdout
            assert str(nb_simple_path) in detach_result_raw.stdout

    def test_init_simple(self, runner, nb_simple_path, jupyter_server):
        with jupyter_server.start_session(nb_simple_path):
            result = runner.invoke(kishu_app, ["init", str(nb_simple_path)])
            assert result.exit_code == 0
            assert "status='ok'" in result.stdout
            assert str(nb_simple_path) in result.stdout

    def test_checkout_not_initialized(self, runner, nb_simple_path):
        result = runner.invoke(kishu_app, ["checkout", str(nb_simple_path), "abc123"])
        assert result.exit_code == 1
        assert isinstance(result.exception, KishuNotInitializedError)

    def test_checkout_simple(self, runner, nb_simple_path, jupyter_server):
        # Start the notebook session.
        contents = JupyterRuntimeEnv.read_notebook_cell_source(nb_simple_path)
        with jupyter_server.start_session(nb_simple_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Run some notebook cells.
            for i in range(len(contents)):
                notebook_session.run_code(contents[i])

            result = runner.invoke(kishu_app, ["checkout", str(nb_simple_path), "1:0:2"])
        assert result.exit_code == 0
        assert "Checkout 1:0:2 in detach mode." in result.stdout

    def test_checkout_reattach(self, runner, nb_simple_path, jupyter_server):
        # Start the notebook session.
        notebook_path = nb_simple_path
        contents = JupyterRuntimeEnv.read_notebook_cell_source(notebook_path)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run the kishu init cell.
            notebook_session.run_code(KISHU_INIT_STR, silent=True)

            # Run some notebook cells.
            for i in range(len(contents)):
                notebook_session.run_code(contents[i])

        with jupyter_server.start_session(notebook_path) as notebook_session:
            # Run some notebook cells, not running init.
            for i in range(len(contents)):
                notebook_session.run_code(contents[i])
            result = runner.invoke(kishu_app, ["checkout", str(nb_simple_path), "1:0:2"])

        assert result.exit_code == 0
        assert "InstrumentStatus.reattach_succeeded: 'reattached'" in result.stdout
        assert str(nb_simple_path) in result.stdout
        assert "Checkout 1:0:2 in detach mode." in result.stdout

    def test_checkout_no_metadata(self, runner, nb_simple_path, jupyter_server):
        with jupyter_server.start_session(nb_simple_path):
            result = runner.invoke(kishu_app, ["checkout", str(nb_simple_path), "abcd123"])
            assert result.exit_code == 1
            assert isinstance(result.exception, KishuNotInitializedError)

    def test_log_non_existent(self, runner):
        result = runner.invoke(kishu_app, ["log", "NON_EXISTENT_NOTEBOOK_ID"])
        assert result.exit_code == 1
        assert isinstance(result.exception, NotebookNotFoundError)
        assert "NON_EXISTENT_NOTEBOOK_ID" in str(result.exception)

    def test_log_not_notebook(self, runner, tmp_path):
        # Create a non-notebook file
        not_notebook_path = tmp_path / "not_notebook.txt"
        not_notebook_path.touch()

        result = runner.invoke(kishu_app, ["log", str(not_notebook_path)])
        assert result.exit_code == 1
        assert isinstance(result.exception, PathIsNotNotebookError)
        assert str(not_notebook_path) in str(result.exception)

    def test_log_basic(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["log", basic_notebook])
        assert result.exit_code == 0
        for commit_id in basic_execution_ids:
            assert commit_id in result.stdout

    def test_log_all_basic(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["log", "--all", basic_notebook])
        assert result.exit_code == 0
        for commit_id in basic_execution_ids:
            assert commit_id in result.stdout

    def test_log_graph_basic(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["log", "--graph", basic_notebook])
        assert result.exit_code == 0
        for commit_id in basic_execution_ids:
            assert commit_id in result.stdout

    def test_log_all_graph_basic(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["log", "--all", "--graph", basic_notebook])
        assert result.exit_code == 0
        for commit_id in basic_execution_ids:
            assert commit_id in result.stdout

    def test_log_with_tag(self, runner, basic_notebook, basic_execution_ids):
        tag = "tag_1"
        result = runner.invoke(kishu_app, ["tag", basic_notebook, tag])
        assert result.exit_code == 0
        assert tag in result.stdout
        assert basic_execution_ids[-1] in result.stdout
        result = runner.invoke(kishu_app, ["log", basic_notebook])
        assert result.exit_code == 0
        for commit_id in basic_execution_ids:
            assert commit_id in result.stdout

    def test_status(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["status", basic_notebook, basic_execution_ids[0]])
        assert result.exit_code == 0
        assert basic_execution_ids[0] in result.stdout

    def test_create_branch(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["branch", basic_notebook, "-c", "new_branch"])
        assert result.exit_code == 0
        assert "new_branch" in result.stdout

    def test_delete_non_checked_out_branch(self, runner, basic_notebook, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", basic_notebook, "-c", "branch_to_keep", basic_execution_ids[-2]])
        runner.invoke(kishu_app, ["branch", basic_notebook, "-c", "branch_to_delete", basic_execution_ids[-1]])
        result = runner.invoke(kishu_app, ["checkout", basic_notebook, "branch_to_keep"])
        assert result.exit_code == 0

        result = runner.invoke(kishu_app, ["branch", basic_notebook, "-d", "branch_to_delete"])
        assert result.exit_code == 0
        assert "Branch branch_to_delete deleted." in result.stdout

    def test_delete_checked_out_branch(self, runner, basic_notebook, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", basic_notebook, "-c", "branch_to_delete"])  # Checked out branch

        result = runner.invoke(kishu_app, ["branch", basic_notebook, "-d", "branch_to_delete"])
        assert result.exit_code == 0
        assert "Cannot delete the currently checked-out branch." in result.stdout

    def test_delete_nonexisting_branch(self, runner, basic_notebook):
        result = runner.invoke(kishu_app, ["branch", basic_notebook, "-d", "NON_EXISTENT_BRANCH"])
        assert result.exit_code == 0
        assert "The provided branch 'NON_EXISTENT_BRANCH' does not exist." in result.stdout

    def test_rename_branch(self, runner, basic_notebook, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", basic_notebook, "-c", "old_name"])
        result = runner.invoke(kishu_app, ["branch", basic_notebook, "-m", "old_name", "new_name"])
        assert result.exit_code == 0
        assert "Branch renamed from old_name to new_name." in result.stdout

    def test_rename_non_existing_branch(self, runner, basic_notebook):
        result = runner.invoke(kishu_app, ["branch", basic_notebook, "-m", "NON_EXISTENT_BRANCH", "new_name"])
        assert result.exit_code == 0
        assert "The provided branch 'NON_EXISTENT_BRANCH' does not exist." in result.stdout

    def test_rename_to_existing_branch(self, runner, basic_notebook, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", basic_notebook, "-c", "old_name"])
        runner.invoke(kishu_app, ["branch", basic_notebook, "-c", "existing_name"])
        result = runner.invoke(kishu_app, ["branch", basic_notebook, "-m", "old_name", "existing_name"])
        assert result.exit_code == 0
        assert "The provided new branch name already exists." in result.stdout

    def test_create_tag_head(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_1"])
        assert result.exit_code == 0
        assert "tag_1" in result.stdout
        assert basic_execution_ids[-1] in result.stdout

    def test_create_tag_specific(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_1", basic_execution_ids[1]])
        assert result.exit_code == 0
        assert "tag_1" in result.stdout
        assert basic_execution_ids[1] in result.stdout

    def test_create_tag_message(self, runner, basic_notebook, basic_execution_ids):
        tag_message = "Tagging for test_create_tag_message"
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_1", "-m", tag_message])
        assert result.exit_code == 0
        assert "tag_1" in result.stdout
        assert basic_execution_ids[-1] in result.stdout
        assert tag_message in result.stdout

    def test_tag_list(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_1"])
        assert result.exit_code == 0
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_2"])
        assert result.exit_code == 0
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_3"])
        assert result.exit_code == 0

        result = runner.invoke(kishu_app, ["tag", basic_notebook, "-l"])
        assert result.exit_code == 0
        assert "tag_1" in result.stdout
        assert "tag_2" in result.stdout
        assert "tag_3" in result.stdout

    def test_delete_tag(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_1"])
        assert result.exit_code == 0

        result = runner.invoke(kishu_app, ["tag", basic_notebook, "-d", "tag_1"])
        assert result.exit_code == 0
        assert "Tag tag_1 deleted." in result.stdout

    def test_delete_tag_nonexisting(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_app, ["tag", basic_notebook, "tag_1"])
        assert result.exit_code == 0

        result = runner.invoke(kishu_app, ["tag", basic_notebook, "-d", "NON_EXISTENT_TAG"])
        assert result.exit_code == 0
        assert "The provided tag 'NON_EXISTENT_TAG' does not exist." in result.stdout

    def test_fegraph(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_experimental_app, ["fegraph", basic_notebook])
        assert result.exit_code == 0
        for commit_id in basic_execution_ids:
            assert commit_id in result.stdout

    def test_fecommit(self, runner, basic_notebook, basic_execution_ids):
        result = runner.invoke(kishu_experimental_app, ["fecommit", basic_notebook, basic_execution_ids[0]])
        assert result.exit_code == 0
        assert basic_execution_ids[0] in result.stdout

    @pytest.mark.parametrize("notebook_names", [[], ["simple.ipynb"], ["simple.ipynb", "numpy.ipynb"]])
    def test_list_with_server(
        self,
        runner,
        tmp_nb_path,
        jupyter_server,
        notebook_names: List[str],
    ):
        # Start sessions and run kishu init cell in each of these sessions.
        for notebook_name in notebook_names:
            with jupyter_server.start_session(tmp_nb_path(notebook_name), persist=True) as notebook_session:
                notebook_session.run_code(KISHU_INIT_STR, silent=True)

        # Kishu should be able to see these sessions.
        # json.loads is used here instead of ListResult.from_json as mypy complains ListResult has no from_json.
        result = runner.invoke(kishu_app, ["list"])
        assert result.exit_code == 0
        for notebook_name in notebook_names:
            assert notebook_name in result.stdout

    def test_list_with_server_no_init(
        self,
        runner,
        tmp_nb_path,
        jupyter_server,
        notebook_name="simple.ipynb",
    ):
        with jupyter_server.start_session(tmp_nb_path(notebook_name)):
            # Kishu should not be able to see this session as "kishu init" was not executed.
            result = runner.invoke(kishu_app, ["list"])
            assert result.exit_code == 0
            assert notebook_name not in result.stdout

    def test_commit_message(
        self,
        runner,
        tmp_nb_path,
        jupyter_server,
        notebook_name="simple.ipynb",
    ):
        notebook_path = tmp_nb_path(notebook_name)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            result = runner.invoke(kishu_app, ["commit", str(notebook_path), "-m", "Test message"])
            assert result.exit_code == 0

    @pytest.mark.parametrize(
        "edit_flag",
        [
            "-e",
            "--edit-branch-name",
            "--edit_branch_name",
            "--edit-commit-id",
            "--edit_commit_id",
        ],
    )
    def test_edit_commit_message(
        self,
        runner,
        tmp_nb_path,
        jupyter_server,
        edit_flag,
        notebook_name="simple.ipynb",
    ):
        notebook_path = tmp_nb_path(notebook_name)
        with jupyter_server.start_session(notebook_path) as notebook_session:
            notebook_session.run_code(KISHU_INIT_STR, silent=True)
            notebook_session.run_code("x = 1")
            result = runner.invoke(kishu_app, ["branch", str(notebook_path), "-c", "new_branch"])
            assert result.exit_code == 0
            assert "new_branch" in result.stdout
            result = runner.invoke(kishu_app, ["commit", str(notebook_path), edit_flag, "new_branch", "-m", "Test message"])
            assert result.exit_code == 0
