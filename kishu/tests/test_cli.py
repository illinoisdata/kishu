import pytest

from typer.testing import CliRunner
from typing import Generator

from kishu import __app_name__, __version__
from kishu.exceptions import (
    NotNotebookPathOrKey,
)
from kishu.cli import kishu_app
from kishu.commands import (
    DetachResult,
    ListResult,
    InitResult,
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
