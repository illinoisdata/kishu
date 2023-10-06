import pytest

from typer.testing import CliRunner
from typing import Generator

from kishu import __app_name__, __version__
from kishu.cli import kishu_app


@pytest.fixture()
def runner() -> Generator[CliRunner, None, None]:
    yield CliRunner()


class TestKishuApp:

    def test_version(self, runner):
        result = runner.invoke(kishu_app, ["--version"])
        assert result.exit_code == 0
        assert f"{__app_name__} v{__version__}\n" in result.stdout

    def test_v(self, runner):
        result = runner.invoke(kishu_app, ["-v"])
        assert result.exit_code == 0
        assert f"{__app_name__} v{__version__}\n" in result.stdout
