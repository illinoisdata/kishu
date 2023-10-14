from __future__ import annotations

import pathlib

from pathlib import Path

from kishu.utils import JupyterRuntimeEnv, enclosing_kernel_id


class NotebookId:
    """
    Holds a notebook's key, path, and kernel id, enabling easy translation between the three
    """
    def __init__(self, key: str, path: Path, kernel_id: str):
        self._key = key
        self._path = path
        self._kernel_id = kernel_id

    @staticmethod
    def from_key(key: str) -> NotebookId:
        try:
            kernel_id = enclosing_kernel_id()
        except Exception as e:
            print(f"WARNING: Skipped retrieving connection info due to {repr(e)}.")
            kernel_id = None
        path = JupyterRuntimeEnv.notebook_path_from_kernel(kernel_id)
        return NotebookId(key=key, path=path, kernel_id=kernel_id)

    @staticmethod
    def from_key_and_path(key: str, path: Path) -> NotebookId:
        try:
            kernel_id = enclosing_kernel_id()
        except Exception as e:
            print(f"WARNING: Skipped retrieving connection info due to {repr(e)}.")
            kernel_id = None
        return NotebookId(key=key, path=path, kernel_id=kernel_id)

    def key(self) -> str:
        return self._key

    def path(self) -> pathlib.Path:
        return self._path

    def kernel_id(self) -> str:
        return self._kernel_id
