import pytest
import time

from typer.testing import CliRunner
from typing import Generator, List

from tests.helpers.nbexec import KISHU_INIT_STR, NB_DIR

from kishu import __app_name__, __version__
from kishu.exceptions import (
    NotNotebookPathOrKey,
)
from kishu.cli import kishu_app
from kishu.commands import (
    DetachResult,
    ListResult,
    InitResult,
    BranchResult,
    DeleteBranchResult,
    RenameBranchResult,
)


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

    def test_list_empty(self, runner, tmp_kishu_path):
        result = runner.invoke(kishu_app, ["list"])
        assert result.exit_code == 0
        assert ListResult.from_json(result.stdout) == ListResult(sessions=[])

        result = runner.invoke(kishu_app, ["list", "-a"])
        assert result.exit_code == 0
        assert ListResult.from_json(result.stdout) == ListResult(sessions=[])

        result = runner.invoke(kishu_app, ["list", "--all"])
        assert result.exit_code == 0
        assert ListResult.from_json(result.stdout) == ListResult(sessions=[])

    def test_init_empty(self, runner, tmp_kishu_path):
        result = runner.invoke(kishu_app, ["init", "non_existent_notebook.ipynb"])
        assert result.exit_code == 0
        init_result = InitResult.from_json(result.stdout)
        assert init_result == InitResult(
            status="error",
            message="FileNotFoundError: Kernel for the notebook not found.",
        )

    def test_detach_empty(self, runner, tmp_kishu_path):
        result = runner.invoke(kishu_app, ["detach", "non_existent_notebook.ipynb"])
        assert result.exit_code == 0
        detach_result = DetachResult.from_json(result.stdout)
        assert detach_result == DetachResult(
            status="error",
            message="FileNotFoundError: Kernel for the notebook not found.",
        )

    def test_detach_simple(self, runner, tmp_kishu_path, nb_simple_path):
        init_result_raw = runner.invoke(kishu_app, ["init", str(nb_simple_path)])
        assert init_result_raw.exit_code == 0
        detach_result_raw = runner.invoke(kishu_app, ["detach", str(nb_simple_path)])
        assert detach_result_raw.exit_code == 0

        # TODO: This should pass with Jupyter Server
        detach_result = DetachResult.from_json(detach_result_raw.stdout)
        assert detach_result == DetachResult(
            status="error",
            message="FileNotFoundError: Kernel for the notebook not found.",
        )

    def test_init_simple(self, runner, tmp_kishu_path, nb_simple_path):
        result = runner.invoke(kishu_app, ["init", str(nb_simple_path)])
        assert result.exit_code == 0

        # TODO: This should pass with Jupyter Server
        init_result = InitResult.from_json(result.stdout)
        assert init_result == InitResult(
            status="error",
            message="FileNotFoundError: Kernel for the notebook not found.",
        )

    def test_log_empty(self, runner, tmp_kishu_path):
        result = runner.invoke(kishu_app, ["log", "NON_EXISTENT_NOTEBOOK_ID"])
        assert result.exit_code == 1
        assert isinstance(result.exception, NotNotebookPathOrKey)
        assert "NON_EXISTENT_NOTEBOOK_ID" in str(result.exception)

    def test_create_branch(self, runner, tmp_kishu_path, notebook_key, basic_execution_ids):
        result = runner.invoke(kishu_app, ["branch", notebook_key, "-c", "new_branch"])
        assert result.exit_code == 0
        branch_result = BranchResult.from_json(result.stdout)
        assert branch_result == BranchResult(
            status="ok",
            branch_name="new_branch",
            commit_id=branch_result.commit_id,  # Not tested
            head=branch_result.head,  # Not tested
        )

    def test_delete_non_checked_out_branch(self, runner, tmp_kishu_path, notebook_key, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", notebook_key, basic_execution_ids[-2], "-c", "branch_to_keep"])
        runner.invoke(kishu_app, ["branch", notebook_key, basic_execution_ids[-1], "-c", "branch_to_delete"])
        result = runner.invoke(kishu_app, ["checkout", notebook_key, "branch_to_keep"])
        assert result.exit_code == 0

        result = runner.invoke(kishu_app, ["branch", notebook_key, "-d", "branch_to_delete"])
        assert result.exit_code == 0
        delete_branch_result = DeleteBranchResult.from_json(result.stdout)
        assert delete_branch_result == DeleteBranchResult(
            status="ok",
            message="Branch branch_to_delete deleted.",
        )

    def test_delete_checked_out_branch(self, runner, tmp_kishu_path, notebook_key, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", notebook_key, "-c", "branch_to_delete"])  # Checked out branch

        result = runner.invoke(kishu_app, ["branch", notebook_key, "-d", "branch_to_delete"])
        assert result.exit_code == 0
        delete_branch_result = DeleteBranchResult.from_json(result.stdout)
        assert delete_branch_result == DeleteBranchResult(
            status="error",
            message="Cannot delete the currently checked-out branch.",
        )

    def test_delete_nonexisting_branch(self, runner, tmp_kishu_path, kishu_jupyter):
        result = runner.invoke(kishu_app, ["branch", kishu_jupyter._notebook_id.key(), "-d", "NON_EXISTENT_BRANCH"])
        assert result.exit_code == 0
        delete_branch_result = DeleteBranchResult.from_json(result.stdout)
        assert delete_branch_result == DeleteBranchResult(
            status="error",
            message="The provided branch 'NON_EXISTENT_BRANCH' does not exist.",
        )

    def test_rename_branch(self, runner, tmp_kishu_path, notebook_key, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", notebook_key, "-c", "old_name"])
        result = runner.invoke(kishu_app, ["branch", notebook_key, "-m", "old_name", "new_name"])
        assert result.exit_code == 0
        rename_branch_result = RenameBranchResult.from_json(result.stdout)
        assert rename_branch_result == RenameBranchResult(
            status="ok",
            branch_name="new_name",
            message="Branch renamed from old_name to new_name.",
        )

    def test_rename_non_existing_branch(self, runner, tmp_kishu_path, kishu_jupyter):
        result = runner.invoke(
            kishu_app, ["branch", kishu_jupyter._notebook_id.key(), "-m", "NON_EXISTENT_BRANCH", "new_name"])
        assert result.exit_code == 0
        rename_branch_result = RenameBranchResult.from_json(result.stdout)
        assert rename_branch_result == RenameBranchResult(
            status="error",
            branch_name="",
            message="The provided branch 'NON_EXISTENT_BRANCH' does not exist.",
        )

    def test_rename_to_existing_branch(self, runner, tmp_kishu_path, notebook_key, basic_execution_ids):
        runner.invoke(kishu_app, ["branch", notebook_key, "-c", "old_name"])
        runner.invoke(kishu_app, ["branch", notebook_key, "-c", "existing_name"])
        result = runner.invoke(kishu_app, ["branch", notebook_key, "-m", "old_name", "existing_name"])
        assert result.exit_code == 0
        rename_branch_result = RenameBranchResult.from_json(result.stdout)
        assert rename_branch_result == RenameBranchResult(
            status="error",
            branch_name="",
            message="The provided new branch name already exists.",
        )

    @pytest.mark.parametrize("notebook_names",
                             [[],
                              ["simple.ipynb"],
                              ["simple.ipynb", "numpy.ipynb"]])
    def test_list_with_server(self, runner, jupyter_server, notebook_names: List[str]):
        # Start sessions and run kishu init cell in each of these sessions.
        for notebook_name in notebook_names:
            with jupyter_server.start_session(NB_DIR, notebook_name) as notebook_session:
                notebook_session.run_code(KISHU_INIT_STR)

        time.sleep(0.5)

        # Kishu should be able to see these sessions.
        result = runner.invoke(kishu_app, ["list"])
        assert result.exit_code == 0
        list_result = ListResult.from_json(result.stdout)
        assert len(list_result.sessions) == len(notebook_names)

        # The notebook names reported by Kishu list should match those at the server side.
        kishu_list_notebook_names = [session.notebook_path.split("/")[-1] for session in list_result.sessions]
        assert set(notebook_names) == set(kishu_list_notebook_names)

    def test_list_with_server_no_init(self, runner, jupyter_server, notebook_name="simple.ipynb"):
        # Start the session.
        jupyter_server.start_session(NB_DIR, notebook_name)

        # Kishu should not be able to see this session as "kishu init" was not executed.
        result = runner.invoke(kishu_app, ["list"])
        assert result.exit_code == 0
        assert ListResult.from_json(result.stdout) == ListResult(sessions=[])
