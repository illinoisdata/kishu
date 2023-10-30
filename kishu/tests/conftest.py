import json
import os
import pytest
import shutil

from pathlib import Path, PurePath
from typing import Generator, Type
from unittest.mock import patch

from kishu.backend import app as kishu_app
from kishu.storage.path import ENV_KISHU_PATH_ROOT, KishuPath
from tests.helpers.nbexec import NB_DIR


"""
Kishu Resources
"""


# Use this fixture to mount Kishu in a temporary directory in the same process.
@pytest.fixture()
def tmp_kishu_path(tmp_path: Path) -> Generator[Type[KishuPath], None, None]:
    original_root = KishuPath.ROOT
    KishuPath.ROOT = str(tmp_path)
    yield KishuPath
    KishuPath.ROOT = original_root


# Use this fixture to mount Kishu in a temporary directory across processes.
@pytest.fixture()
def tmp_kishu_path_os(tmp_path: Path) -> Generator[Type[KishuPath], None, None]:
    original_root = os.environ.get(ENV_KISHU_PATH_ROOT, None)
    os.environ[ENV_KISHU_PATH_ROOT] = str(tmp_path)
    yield KishuPath
    if original_root is not None:
        os.environ[ENV_KISHU_PATH_ROOT] = original_root


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
def nb_simple_path(tmp_path: Path, kishu_test_dir: Path) -> Path:
    real_nb_path = kishu_test_dir / PurePath(KISHU_TEST_NOTEBOOKS_DIR, "simple.ipynb")
    tmp_nb_path = tmp_path / PurePath("simple.ipynb")
    shutil.copy(real_nb_path, tmp_nb_path)
    return tmp_nb_path


"""
Jupyter runtime mocks
"""


# Mock Jupyter server info.
MOCK_SERVER = {
    'url': 'http://localhost:8888/',
    'token': 'token_value',
    'pid': 12345,
    'root_dir': '/root/',
    'notebook_dir': '/notebooks/'
}

# Mock Jupyter session info.
MOCK_SESSION = {
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
def mock_servers():
    with patch('kishu.runtime.Path.read_bytes', return_value=json.dumps(MOCK_SERVER).encode()), \
         patch('kishu.runtime.psutil.pid_exists', return_value=True), \
         patch('kishu.runtime.Path.glob', side_effect=glob_side_effect), \
         patch("kishu.runtime.jupyter_core.paths.jupyter_runtime_dir", return_value=Path("/")), \
         patch('kishu.runtime.urllib.request.urlopen') as mock_urlopen:

        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps([MOCK_SESSION]).encode()
        yield [MOCK_SERVER]


def create_temporary_copy(path: str, filename: str, temp_dir: str):
    temp_path = os.path.join(temp_dir, filename)
    shutil.copy2(path, temp_path)
    return temp_path


# Sets TEST_NOTEBOOK_PATH environment variable to be the path to a temporary copy of a notebook
@pytest.fixture
def set_temp_notebook_path_env(tmp_path, request):
    notebook_name = getattr(request, "param", "simple.ipynb")
    path_to_notebook = os.getcwd()
    notebook_full_path = os.path.join(path_to_notebook, NB_DIR, notebook_name)
    temp_path = create_temporary_copy(notebook_full_path, notebook_name, tmp_path)

    os.environ["TEST_NOTEBOOK_PATH"] = temp_path

    yield temp_path

    del os.environ["TEST_NOTEBOOK_PATH"]


# Sets TEST_NOTEBOOK_PATH environment variable to be the path to a real notebook
@pytest.fixture
def set_real_notebook_path_env(request):
    notebook_name = getattr(request, "param", "simple.ipynb")
    path_to_notebook = os.getcwd()
    notebook_full_path = os.path.join(path_to_notebook, NB_DIR, notebook_name)

    os.environ["TEST_NOTEBOOK_PATH"] = notebook_full_path

    yield notebook_full_path

    del os.environ["TEST_NOTEBOOK_PATH"]
