import pytest
import json
from unittest.mock import patch
from pathlib import Path
from kishu.utils import IPythonSession, JupyterRuntimeEnv, enclosing_kernel_id, _iter_maybe_running_servers, \
    _iter_maybe_sessions, _get_sessions, _iter_sessions


MOCK_SERVER = {
        'url': 'http://localhost:8888/',
        'token': 'token_value',
        'pid': 12345,
        'root_dir': '/root/',
        'notebook_dir': '/notebooks/'
    }

MOCK_SESSION = {
        'notebook': {'path': 'notebook1.ipynb'},
        'kernel': {'id': 'kernel_id'}
    }


@pytest.fixture
def mock_servers():
    return [
        {
            "url": "http://localhost:8888/",
            "token": "token_value",
            "pid": 12345,
            "root_dir": "/root/",
            "notebook_dir": "/notebooks/"
        }
    ]


@pytest.fixture
def mock_sessions():
    return [
        {
            "kernel": {
                "id": "kernel_id_1"
            },
            "notebook": {
                "path": "notebook1.ipynb"
            }
        },
        {
            "kernel": {
                "id": "kernel_id_2"
            },
            "notebook": {
                "path": "notebook2.ipynb"
            }
        }
    ]


def glob_side_effect(pattern):
    if "nbserver" in pattern:
        return [Path("tests/notebooks/simple.ipynb")]
    return []


def test_iter_maybe_running_servers(mock_servers):
    with patch('kishu.utils.json.loads', return_value=mock_servers[0]), \
         patch('kishu.utils.psutil.pid_exists', return_value=True), \
         patch('kishu.utils.Path.glob', side_effect=glob_side_effect), \
         patch("kishu.utils.jupyter_core.paths.jupyter_runtime_dir", return_value = Path("/")):
        result = list(_iter_maybe_running_servers())

    assert result == mock_servers


def test_server_with_sessions():
    with patch('kishu.utils._iter_maybe_running_servers', return_value=[MOCK_SERVER]), \
         patch('kishu.utils.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps([MOCK_SESSION])
        sessions = list(_iter_maybe_sessions())
        assert sessions == [(MOCK_SERVER, MOCK_SESSION)]


def test_enclosing_kernel_id():
    with patch('kishu.utils.ipykernel.get_connection_file', return_value="kernel-kernel_id_1.json"):
        result = enclosing_kernel_id()
    assert result == "kernel_id_1"


def test_notebook_path_from_kernel(mock_servers, mock_sessions):
    with patch(
            'kishu.utils._iter_sessions',
            return_value=iter([IPythonSession("kernel_id_1", Path("/root/notebook1.ipynb"))])
    ):
        env = JupyterRuntimeEnv()
        result = env.notebook_path_from_kernel("kernel_id_1")
    assert result == Path("/root/notebook1.ipynb")


def test_session_with_root_dir():
    with patch('kishu.utils._iter_maybe_sessions', return_value=[(MOCK_SERVER, MOCK_SESSION)]):
        sessions = list(_iter_sessions())
        expected_session = IPythonSession(kernel_id='kernel_id', notebook_path=Path('/root/notebook1.ipynb'))
        assert sessions == [expected_session]


def test_session_with_only_notebook_dir():
    with patch('kishu.utils._iter_maybe_sessions', return_value=[(MOCK_SERVER, MOCK_SESSION)]):
        sessions = list(_iter_sessions())
        expected_session = IPythonSession(kernel_id='kernel_id', notebook_path=Path('/root/notebook1.ipynb'))
        assert sessions == [expected_session]


def test_iter_maybe_running_servers_bad_json():
    with patch('kishu.utils.json.loads', side_effect=json.JSONDecodeError("", "", 0)):
        result = list(_iter_maybe_running_servers())
    assert not result  # should return an empty list


def test_get_sessions_raises_exception():
    with patch('kishu.utils.urllib.request.urlopen', side_effect=Exception):
        sessions = _get_sessions({"url": "http://localhost:8888/", "token": "token_value"})
    assert not sessions


def test_enclosing_kernel_id_no_dash():
    with patch('kishu.utils.ipykernel.get_connection_file', return_value="kernel.json"):
        with pytest.raises(FileNotFoundError, match="Failed to identify IPython connection file"):
            enclosing_kernel_id()


def test_enclosing_kernel_id_unexpected_format():
    with patch('kishu.utils.ipykernel.get_connection_file', return_value="unexpected_format.json"):
        with pytest.raises(FileNotFoundError, match="Failed to identify IPython connection file"):
            enclosing_kernel_id()


def test_notebook_path_from_kernel_not_found():
    with patch('kishu.utils._iter_sessions', return_value=iter([])):
        env = JupyterRuntimeEnv()
        with pytest.raises(FileNotFoundError, match="Failed to identify notebook file path."):
            env.notebook_path_from_kernel("non_existent_kernel_id")
