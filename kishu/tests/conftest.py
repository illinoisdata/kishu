import configparser
import dataclasses
import json
import os
import shutil
from pathlib import Path, PurePath
from typing import Any, Callable, Generator, List, Optional, Tuple, Type
from unittest.mock import patch

import matplotlib.pyplot
import numpy
import pandas
import pytest
import requests
import seaborn
from IPython.core.interactiveshell import InteractiveShell

from kishu.jupyterint import KishuForJupyter
from kishu.notebook_id import NotebookId
from kishu.storage.config import Config
from kishu.storage.path import ENV_KISHU_PATH_ROOT, KishuPath
from tests.helpers.serverexec import JupyterServerRunner

"""
Pytest Mods
"""


def pytest_addoption(parser):
    parser.addoption("--run-benchmark", action="store_true", default=False, help="run benchmark tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-benchmark"):
        skip_benchmark = pytest.mark.skip(reason="Enable with --run-benchmark")
        for item in items:
            if "benchmark" in item.keywords:
                item.add_marker(skip_benchmark)


"""
Kishu Resources
"""


@pytest.fixture(autouse=True)
def set_test_mode() -> Generator[None, None, None]:
    original_test_mode = os.environ.get(KishuForJupyter.ENV_KISHU_TEST_MODE, None)
    os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE] = "true"
    yield None
    if original_test_mode is not None:
        os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE] = original_test_mode
    else:
        del os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE]


# Use this fixture to mount Kishu in a temporary directory.
@pytest.fixture(autouse=True)
def tmp_kishu_path(tmp_path: Path) -> Generator[Type[KishuPath], None, None]:
    original_env_root = os.environ.get(ENV_KISHU_PATH_ROOT, None)
    os.environ[ENV_KISHU_PATH_ROOT] = str(tmp_path)
    original_root = KishuPath.ROOT
    KishuPath.ROOT = tmp_path
    yield KishuPath
    KishuPath.ROOT = original_root
    if original_env_root is not None:
        os.environ[ENV_KISHU_PATH_ROOT] = original_env_root
    else:
        del os.environ[ENV_KISHU_PATH_ROOT]


"""
Test Resources: notebooks, test cases, data
"""


@pytest.fixture()
def kishu_test_dir() -> Path:
    return Path(__file__).resolve().parents[0]


KISHU_TEST_NOTEBOOKS_DIR = "notebooks"


@pytest.fixture()
def kishu_test_notebook_dir(kishu_test_dir) -> Path:
    return kishu_test_dir / PurePath(KISHU_TEST_NOTEBOOKS_DIR)


@pytest.fixture()
def tmp_nb_path(tmp_path: Path, kishu_test_notebook_dir: Path) -> Callable[[str], Path]:
    def _tmp_nb_path(notebook_name: str) -> Path:
        real_nb_path = kishu_test_notebook_dir / PurePath(notebook_name)
        tmp_nb_path = tmp_path / PurePath(notebook_name)
        shutil.copy(real_nb_path, tmp_nb_path)
        return tmp_nb_path

    return _tmp_nb_path


@pytest.fixture()
def nb_simple_path(tmp_nb_path: Callable[[str], Path]) -> Path:
    return tmp_nb_path("simple.ipynb")


@pytest.fixture(autouse=True)
def tmp_path_config(tmp_kishu_path) -> Generator[type, None, None]:
    prev_config_path = Config.CONFIG_PATH
    prev_config = Config.config
    prev_last_read_time = Config.last_read_time
    Config.CONFIG_PATH = KishuPath.config_path()
    Config.config = configparser.ConfigParser()
    Config.last_read_time = -1
    Config._create_config_file()
    yield Config
    Config.CONFIG_PATH = prev_config_path
    Config.config = prev_config
    Config.last_read_time = prev_last_read_time


@pytest.fixture()
def enable_incremental_store(tmp_kishu_path) -> Generator[type, None, None]:
    prev_value = Config.get("PLANNER", "incremental_store", True)
    Config.set("PLANNER", "incremental_store", True)
    yield Config
    Config.set("PLANNER", "incremental_store", prev_value)


@pytest.fixture()
def disable_incremental_store(tmp_kishu_path) -> Generator[type, None, None]:
    prev_value = Config.get("PLANNER", "incremental_store", True)
    Config.set("PLANNER", "incremental_store", False)
    yield Config
    Config.set("PLANNER", "incremental_store", prev_value)


@pytest.fixture()
def matplotlib_plot() -> Generator[Tuple[Any, List[matplotlib.lines.Line2D]], None, None]:
    # Setup code
    matplotlib.pyplot.close("all")
    df = pandas.DataFrame(numpy.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=["a", "b", "c"])
    a = matplotlib.pyplot.plot(df["a"], df["b"])
    matplotlib.pyplot.xlabel("XLABEL_1")
    yield matplotlib.pyplot, a

    # Teardown code
    matplotlib.pyplot.close("all")


@pytest.fixture()
def seaborn_distplot() -> Generator[seaborn.axisgrid.FacetGrid, None, None]:
    # Setup code
    df = seaborn.load_dataset("penguins")
    plot1 = seaborn.displot(data=df, x="flipper_length_mm", y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    yield plot1

    # Teardown code
    matplotlib.pyplot.close("all")


@pytest.fixture()
def seaborn_scatterplot() -> Generator[matplotlib.axes._axes.Axes, None, None]:
    # Setup code
    df = seaborn.load_dataset("penguins")
    plot1 = seaborn.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel("flipper_length_mm")
    plot1.set_facecolor("white")

    yield plot1

    # Teardown code
    matplotlib.pyplot.close("all")


"""
Jupyter runtime mocks
"""


# Mock Jupyter server info.
@pytest.fixture
def mock_server_header():
    return {
        "url": "http://localhost:8888/",
        "token": "token_value",
        "pid": 12345,
        "root_dir": "/root/",
        "notebook_dir": "/notebooks/",
    }


# Mock Jupyter session info.
@pytest.fixture
def mock_session_header():
    return {"notebook": {"path": "notebook1.ipynb"}, "kernel": {"id": "test_kernel_id"}}


# Ensures Path.glob() returns the notebook path we want to return
def glob_side_effect(pattern):
    if "nbserver" in pattern:
        return [Path("tests/notebooks/simple.ipynb")]
    return []


# Mocks relevant external dependancies to produce the effect of reading data from servers and sessions
# used to test runtime.py
@pytest.fixture
def mock_servers(mock_server_header, mock_session_header):
    resp = requests.Response()
    resp.status_code = 200
    resp._content = json.dumps([mock_session_header])
    with patch("kishu.jupyter.runtime.Path.read_bytes", return_value=json.dumps(mock_server_header).encode()), patch(
        "kishu.jupyter.runtime.psutil.pid_exists", return_value=True
    ), patch("kishu.jupyter.runtime.Path.glob", side_effect=glob_side_effect), patch(
        "kishu.jupyter.runtime.jupyter_core.paths.jupyter_runtime_dir", return_value=Path("/")
    ), patch(
        "kishu.jupyter.runtime.requests.get", return_value=resp
    ):
        yield [mock_server_header]


def create_temporary_copy(path: str, filename: str, temp_dir: str):
    temp_path = os.path.join(temp_dir, filename)
    shutil.copy2(path, temp_path)
    return temp_path


# Sets TEST_NOTEBOOK_PATH environment variable to be the path to a temporary copy of a notebook
@pytest.fixture
def set_notebook_path_env(tmp_path, kishu_test_notebook_dir, request):
    notebook_name = getattr(request, "param", "simple.ipynb")
    real_nb_path = kishu_test_notebook_dir / PurePath(notebook_name)
    tmp_nb_path = tmp_path / PurePath(notebook_name)
    shutil.copy(real_nb_path, tmp_nb_path)

    os.environ["TEST_NOTEBOOK_PATH"] = str(tmp_nb_path)

    yield str(tmp_nb_path)

    del os.environ["TEST_NOTEBOOK_PATH"]


"""
KishuForJupyter Fixtures
"""


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


@pytest.fixture()
def notebook_key() -> Generator[str, None, None]:
    yield "notebook_123"


@pytest.fixture()
def kishu_jupyter(tmp_kishu_path, notebook_key, set_notebook_path_env) -> Generator[KishuForJupyter, None, None]:
    ip = InteractiveShell()
    kishu_jupyter = KishuForJupyter(notebook_id=NotebookId.from_enclosing_with_key(notebook_key), ip=ip)
    yield kishu_jupyter


@pytest.fixture()
def basic_notebook(kishu_jupyter, set_notebook_path_env) -> Generator[str, None, None]:
    yield set_notebook_path_env


@pytest.fixture()
def basic_notebook_path(basic_notebook) -> Generator[Path, None, None]:
    yield Path(basic_notebook)


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

    yield ["0:0:1", "0:0:2", "0:0:3"]  # List of commit IDs


"""
Jupyter Server Fixtures
"""


@pytest.fixture()
def jupyter_server() -> Generator[JupyterServerRunner, None, None]:
    with JupyterServerRunner() as jupyter_server:
        yield jupyter_server
