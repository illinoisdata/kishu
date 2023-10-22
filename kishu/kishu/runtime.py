import ipykernel
import json
import jupyter_core.paths
import nbformat
import os
import psutil
import urllib.request

from dataclasses import dataclass
from itertools import chain
from pathlib import Path, PurePath
from typing import Generator, Tuple


@dataclass
class IPythonSession:
    kernel_id: str
    notebook_path: Path


def _iter_maybe_running_servers() -> Generator[dict, None, None]:
    runtime_dir = Path(jupyter_core.paths.jupyter_runtime_dir())
    if runtime_dir.is_dir():
        config_files = chain(
            runtime_dir.glob("nbserver-*.json"),  # jupyter notebook (or lab 2)
            runtime_dir.glob("jpserver-*.json"),  # jupyterlab 3
        )
        for file_name in sorted(config_files, key=os.path.getmtime, reverse=True):
            try:
                srv = json.loads(file_name.read_bytes())
                if psutil.pid_exists(srv.get("pid", -1)):
                    # pid_exists always returns False for negative PIDs.
                    yield srv
            except json.JSONDecodeError:
                pass


def _get_sessions(srv: dict):
    try:
        url = f"{srv['url']}api/sessions"
        if srv['token']:
            url += f"?token={srv['token']}"
        with urllib.request.urlopen(url, timeout=1.0) as req:
            sessions = json.load(req)
            return sessions
    except Exception:
        return []


def _iter_maybe_sessions() -> Generator[Tuple[dict, dict], None, None]:
    for srv in _iter_maybe_running_servers():
        for sess in _get_sessions(srv):
            yield srv, sess


class JupyterRuntimeEnv:
    NBFORMAT_VERSION = 4

    @staticmethod
    def enclosing_kernel_id() -> str:
        # TODO needs to be called inside ipython kernel
        if os.environ.get("TEST_NOTEBOOK_PATH"):  # means we are testing
            return "test_kernel_id"
        connection_file_path = ipykernel.get_connection_file()
        connection_file = os.path.basename(connection_file_path)
        if '-' not in connection_file:
            # connection_file not in expected format.
            # TODO: Find more stable way to extract kernel ID.
            raise FileNotFoundError("Failed to identify IPython connection file")
        return connection_file.split('-', 1)[1].split('.')[0]

    @staticmethod
    def iter_sessions() -> Generator[IPythonSession, None, None]:
        for srv, sess in _iter_maybe_sessions():
            relative_path = PurePath(sess["notebook"]["path"])
            yield IPythonSession(
                kernel_id=sess["kernel"]["id"],
                notebook_path=Path(srv.get("root_dir") or srv["notebook_dir"]) / relative_path
            )

    @staticmethod
    def notebook_path_from_kernel(kernel_id: str) -> Path:
        if os.environ.get("TEST_NOTEBOOK_PATH"):
            path_str = os.environ.get("TEST_NOTEBOOK_PATH")
            assert path_str is not None
            return Path(path_str)
        for sess in JupyterRuntimeEnv.iter_sessions():
            if sess.kernel_id == kernel_id:
                return sess.notebook_path
        raise FileNotFoundError("Failed to identify notebook file path.")

    @staticmethod
    def kernel_id_from_notebook(notebook_path: Path) -> str:
        for sess in JupyterRuntimeEnv.iter_sessions():
            if sess.notebook_path.resolve() == notebook_path.resolve():
                return sess.kernel_id
        raise FileNotFoundError("Kernel for the notebook not found.")

    @staticmethod
    def read_notebook(notebook_path: Path) -> nbformat.NotebookNode:
        with open(notebook_path, 'r') as f:
            return nbformat.read(f, JupyterRuntimeEnv.NBFORMAT_VERSION)
