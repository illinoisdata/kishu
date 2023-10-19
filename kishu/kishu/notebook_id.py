from __future__ import annotations

from pathlib import Path
from typing import Optional

from kishu.runtime import JupyterRuntimeEnv


class NotebookId:
    """
    Holds a notebook's key, path, and kernel id, enabling easy translation between the three
    """
    def __init__(self, key: str, path: Path, kernel_id: str):
        self._key = key
        self._path = path
        self._kernel_id = kernel_id

    @staticmethod
    def from_enclosing_with_key(key: str) -> NotebookId:
        kernel_id = JupyterRuntimeEnv.enclosing_kernel_id()
        path = JupyterRuntimeEnv.notebook_path_from_kernel(kernel_id)
        return NotebookId(key=key, path=path, kernel_id=kernel_id)

    def key(self) -> str:
        return self._key

    def path(self) -> Path:
        return self._path

    def kernel_id(self) -> Optional[str]:
        return self._kernel_id

    def set_key(self, new_key: str) -> None:
        self._key = new_key
