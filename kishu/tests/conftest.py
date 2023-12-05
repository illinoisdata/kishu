import dataclasses
import json
import os
import pytest
import requests
import shutil

from IPython.core.interactiveshell import InteractiveShell
from pathlib import Path, PurePath
from typing import Callable, Generator, List, Optional, Type
from unittest.mock import patch

from kishu.backend import app as kishu_app
from kishu.jupyterint import KishuForJupyter
from kishu.notebook_id import NotebookId
from kishu.storage.path import ENV_KISHU_PATH_ROOT, KishuPath

from tests.helpers.serverexec import JupyterServerRunner


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
    original_root = os.environ.get(ENV_KISHU_PATH_ROOT, None)
    os.environ[ENV_KISHU_PATH_ROOT] = str(tmp_path)
    original_root = KishuPath.ROOT
    KishuPath.ROOT = str(tmp_path)
    yield KishuPath
    KishuPath.ROOT = original_root
    if original_root is not None:
        os.environ[ENV_KISHU_PATH_ROOT] = original_root
    else:
        del os.environ[ENV_KISHU_PATH_ROOT]


@pytest.fixture()
def backend_client():
    return kishu_app.test_client()


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


"""
Jupyter runtime mocks
"""


# Mock Jupyter server info.
@pytest.fixture
def mock_server_header():
    return {
        'url': 'http://localhost:8888/',
        'token': 'token_value',
        'pid': 12345,
        'root_dir': '/root/',
        'notebook_dir': '/notebooks/'
    }


# Mock Jupyter session info.
@pytest.fixture
def mock_session_header():
    return {
        'notebook': {'path': 'notebook1.ipynb'},
        'kernel': {'id': 'test_kernel_id'}
    }


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
    with patch('kishu.jupyter.runtime.Path.read_bytes', return_value=json.dumps(mock_server_header).encode()), \
         patch('kishu.jupyter.runtime.psutil.pid_exists', return_value=True), \
         patch('kishu.jupyter.runtime.Path.glob', side_effect=glob_side_effect), \
         patch("kishu.jupyter.runtime.jupyter_core.paths.jupyter_runtime_dir", return_value=Path("/")), \
         patch('kishu.jupyter.runtime.requests.get', return_value=resp):
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


"""
Jupyter Server Fixtures
"""


@pytest.fixture()
def jupyter_server() -> Generator[JupyterServerRunner, None, None]:
    with JupyterServerRunner() as jupyter_server:
        yield jupyter_server
