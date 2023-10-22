import pytest
import json
from unittest.mock import patch
from pathlib import Path
from kishu.runtime import IPythonSession, JupyterRuntimeEnv, _iter_maybe_running_servers, \
    _iter_maybe_sessions, _get_sessions
from .conftest import MOCK_SERVER, MOCK_SESSION


def test_iter_maybe_running_servers(mock_servers):
    result = list(_iter_maybe_running_servers())
    assert result == mock_servers


def test_server_with_sessions(mock_servers):
    sessions = list(_iter_maybe_sessions())
    assert sessions == [(MOCK_SERVER, MOCK_SESSION)]


def test_enclosing_kernel_id(mock_servers):
    with patch('kishu.runtime.ipykernel.get_connection_file', return_value="kernel-kernel_id_1.json"):
        result = JupyterRuntimeEnv.enclosing_kernel_id()
    assert result == "kernel_id_1"


def test_notebook_path_from_kernel(mock_servers):
    result = JupyterRuntimeEnv.notebook_path_from_kernel("kernel_id_1")
    assert result == Path("/root/notebook1.ipynb")


def test_session_with_root_dir(mock_servers):
    sessions = list(JupyterRuntimeEnv.iter_sessions())
    expected_session = IPythonSession(kernel_id='kernel_id_1', notebook_path=Path('/root/notebook1.ipynb'))
    assert sessions == [expected_session]


def test_kernel_id_from_notebook(mock_servers):
    kernel_id = JupyterRuntimeEnv.kernel_id_from_notebook(Path("/root/notebook1.ipynb"))
    assert kernel_id == "kernel_id_1"


def test_iter_maybe_running_servers_bad_json():
    with patch('kishu.runtime.json.loads', side_effect=json.JSONDecodeError("", "", 0)):
        result = list(_iter_maybe_running_servers())
    assert not result  # should return an empty list


def test_get_sessions_raises_exception():
    with patch('kishu.runtime.urllib.request.urlopen', side_effect=Exception):
        sessions = _get_sessions({"url": "http://localhost:8888/", "token": "token_value"})
    assert not sessions


def test_enclosing_kernel_id_no_dash():
    with patch('kishu.runtime.ipykernel.get_connection_file', return_value="kernel.json"):
        with pytest.raises(FileNotFoundError, match="Failed to identify IPython connection file"):
            JupyterRuntimeEnv.enclosing_kernel_id()


def test_enclosing_kernel_id_unexpected_format():
    with patch('kishu.runtime.ipykernel.get_connection_file', return_value="unexpected_format.json"):
        with pytest.raises(FileNotFoundError, match="Failed to identify IPython connection file"):
            JupyterRuntimeEnv.enclosing_kernel_id()


def test_notebook_path_from_kernel_not_found():
    with pytest.raises(FileNotFoundError, match="Failed to identify notebook file path."):
        JupyterRuntimeEnv.notebook_path_from_kernel("non_existent_kernel_id")