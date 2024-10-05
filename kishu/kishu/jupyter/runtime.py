from __future__ import annotations

import json
import os
from dataclasses import dataclass
from itertools import chain
from pathlib import Path, PurePath
from typing import Dict, Generator, List, Optional, Tuple

import ipykernel
import jupyter_core.paths
import nbformat
import psutil
import requests


class JupyterRuntimeContextHandler:
    def __init__(self, cookies: Dict[str, str]) -> None:
        self.cookies = cookies
        self.prev_cookies = cookies

    def __enter__(self) -> JupyterRuntimeContextHandler:
        self.prev_cookies = JupyterRuntimeEnv.COOKIES
        JupyterRuntimeEnv.COOKIES = self.cookies
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        JupyterRuntimeEnv.COOKIES = self.prev_cookies


@dataclass
class IPythonSession:
    kernel_id: str
    notebook_path: Path


class JupyterRuntimeEnv:
    NBFORMAT_VERSION = 4
    COOKIES: Dict[str, str] = {}

    @staticmethod
    def context(cookies: Optional[Dict[str, str]] = None) -> JupyterRuntimeContextHandler:
        return JupyterRuntimeContextHandler(
            cookies=cookies if cookies is not None else JupyterRuntimeEnv.COOKIES,
        )

    @staticmethod
    def enclosing_kernel_id() -> str:
        # TODO needs to be called inside ipython kernel
        if os.environ.get("TEST_NOTEBOOK_PATH"):  # means we are testing
            return "test_kernel_id"
        connection_file_path = ipykernel.get_connection_file()
        connection_file = os.path.basename(connection_file_path)
        if "-" not in connection_file:
            # connection_file not in expected format.
            # TODO: Find more stable way to extract kernel ID.
            raise FileNotFoundError("Failed to identify IPython connection file")
        return connection_file.split("-", 1)[1].split(".")[0]

    @staticmethod
    def iter_maybe_running_servers() -> Generator[dict, None, None]:
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

    @staticmethod
    def get_sessions(srv: dict):
        try:
            url = f"{srv['url']}api/sessions"
            if srv["token"]:
                url += f"?token={srv['token']}"
            resp = requests.get(
                url,
                cookies=JupyterRuntimeEnv.COOKIES,
                timeout=1.0,
            )
            return [] if not resp.ok else json.loads(resp.content)
        except Exception:
            return []

    @staticmethod
    def iter_maybe_sessions() -> Generator[Tuple[dict, dict], None, None]:
        for srv in JupyterRuntimeEnv.iter_maybe_running_servers():
            for sess in JupyterRuntimeEnv.get_sessions(srv):
                yield srv, sess

    @staticmethod
    def iter_sessions() -> Generator[IPythonSession, None, None]:
        for srv, sess in JupyterRuntimeEnv.iter_maybe_sessions():
            relative_path = PurePath(sess["notebook"]["path"])
            yield IPythonSession(
                kernel_id=sess["kernel"]["id"], notebook_path=Path(srv.get("root_dir") or srv["notebook_dir"]) / relative_path
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
        with open(notebook_path, "r") as f:
            return nbformat.read(f, JupyterRuntimeEnv.NBFORMAT_VERSION)

    @staticmethod
    def read_notebook_cell_source(notebook_path: Path) -> List[str]:
        nb = JupyterRuntimeEnv.read_notebook(notebook_path)
        return [
            cell["source"]
            for cell in nb.get("cells", {})
            if "source" in cell and cell["cell_type"] == "code"  # We don't need non-code cells in test cases
        ]
