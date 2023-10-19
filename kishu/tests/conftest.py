import json
import os
import pytest
import shutil

from pathlib import Path
from typing import Generator, Type
from unittest.mock import patch

from kishu.backend import app as kishu_app
from kishu.storage.path import ENV_KISHU_PATH_ROOT, KishuPath
from tests.helpers.nbexec import NB_DIR


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


MOCK_SERVER = {
        'url': 'http://localhost:8888/',
        'token': 'token_value',
        'pid': 12345,
        'root_dir': '/root/',
        'notebook_dir': '/notebooks/'
    }

MOCK_SESSION = {
        'notebook': {'path': 'notebook1.ipynb'},
        'kernel': {'id': 'kernel_id_1'}
    }


def glob_side_effect(pattern):
    if "nbserver" in pattern:
        return [Path("tests/notebooks/simple.ipynb")]
    return []


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


@pytest.fixture
def set_notebook_path_env(tmp_path, request):
    """
    Sets notebook_path environment variable to be the path to a temporary copy of a notebook
    """
    notebook_name = getattr(request, "param", "simple.ipynb")
    path_to_notebook = os.getcwd()
    notebook_full_path = os.path.join(path_to_notebook, NB_DIR, notebook_name)
    temp_path = create_temporary_copy(notebook_full_path, notebook_name, tmp_path)

    os.environ['notebook_path'] = temp_path

    yield temp_path

    del os.environ['notebook_path']
