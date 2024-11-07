import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kishu.jupyter.runtime import IPythonSession, JupyterRuntimeEnv


def test_iter_maybe_running_servers(mock_servers):
    result = list(JupyterRuntimeEnv.iter_maybe_running_servers())
    assert result == mock_servers


def test_server_with_sessions(mock_server_header, mock_session_header, mock_servers):
    sessions = list(JupyterRuntimeEnv.iter_maybe_sessions())
    assert sessions == [(mock_server_header, mock_session_header)]


def test_enclosing_kernel_id(mock_servers):
    with patch("kishu.jupyter.runtime.ipykernel.get_connection_file", return_value="kernel-test_kernel_id.json"):
        result = JupyterRuntimeEnv.enclosing_kernel_id()
    assert result == "test_kernel_id"


def test_notebook_path_from_kernel(mock_servers):
    result = JupyterRuntimeEnv.notebook_path_from_kernel("test_kernel_id")
    assert result == Path("/root/notebook1.ipynb")


def test_session_with_root_dir(mock_servers):
    sessions = list(JupyterRuntimeEnv.iter_sessions())
    expected_session = IPythonSession(kernel_id="test_kernel_id", notebook_path=Path("/root/notebook1.ipynb"))
    assert sessions == [expected_session]


def test_kernel_id_from_notebook(mock_servers):
    kernel_id = JupyterRuntimeEnv.kernel_id_from_notebook(Path("/root/notebook1.ipynb"))
    assert kernel_id == "test_kernel_id"


def test_iter_maybe_running_servers_bad_json():
    with patch("kishu.jupyter.runtime.json.loads", side_effect=json.JSONDecodeError("", "", 0)):
        result = list(JupyterRuntimeEnv.iter_maybe_running_servers())
    assert not result  # should return an empty list


def test_get_sessions_raises_exception():
    with patch("kishu.jupyter.runtime.requests.get", side_effect=Exception):
        sessions = JupyterRuntimeEnv.get_sessions({"url": "http://localhost:8888/", "token": "token_value"})
    assert not sessions


def test_enclosing_kernel_id_no_dash():
    with patch("kishu.jupyter.runtime.ipykernel.get_connection_file", return_value="kernel.json"):
        with pytest.raises(FileNotFoundError, match="Failed to identify IPython connection file"):
            JupyterRuntimeEnv.enclosing_kernel_id()


def test_enclosing_kernel_id_unexpected_format():
    with patch("kishu.jupyter.runtime.ipykernel.get_connection_file", return_value="unexpected_format.json"):
        with pytest.raises(FileNotFoundError, match="Failed to identify IPython connection file"):
            JupyterRuntimeEnv.enclosing_kernel_id()


def test_notebook_path_from_kernel_not_found():
    with pytest.raises(FileNotFoundError, match="Failed to identify notebook file path."):
        JupyterRuntimeEnv.notebook_path_from_kernel("non_existent_kernel_id")
