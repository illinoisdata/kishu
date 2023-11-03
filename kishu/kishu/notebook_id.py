from __future__ import annotations

import json
import nbformat
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
from datetime import datetime
from pathlib import Path
from typing import Optional

from kishu.exceptions import (
    MissingNotebookMetadataError,
    NotNotebookPathOrKey,
)
from kishu.runtime import JupyterRuntimeEnv
from kishu.storage.path import KishuPath


@dataclass
class KishuNotebookMetadata:
    notebook_id: str
    session_count: int = 0


@dataclass_json
@dataclass
class JupyterConnectionInfo:
    kernel_id: str
    notebook_path: str


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

    @staticmethod
    def parse_key_from_path(path: Path) -> str:
        nb = JupyterRuntimeEnv.read_notebook(path)
        metadata = NotebookId.read_kishu_metadata(nb)
        return metadata.notebook_id

    @staticmethod
    def parse_key_from_path_or_key(path_or_key: str) -> str:
        # Try parsing as path, if exists.
        path = Path(path_or_key)
        if path.exists():
            return NotebookId.parse_key_from_path(path)

        # Notebook path does not exist, try parsing as key.
        key = path_or_key
        if KishuPath.exists(key):
            return key

        raise NotNotebookPathOrKey(path_or_key)

    def key(self) -> str:
        return self._key

    def path(self) -> Path:
        return self._path

    def kernel_id(self) -> str:
        return self._kernel_id

    """
    Kishu notebook metadata.
    """

    @staticmethod
    def write_kishu_metadata(nb: nbformat.NotebookNode) -> KishuNotebookMetadata:
        if "kishu" not in nb.metadata:
            # Create new Kishu metadata.
            notebook_name = datetime.now().strftime('%Y%m%dT%H%M%S')
            metadata = KishuNotebookMetadata(notebook_name)
        else:
            # Read existing Kishu metadata
            metadata = KishuNotebookMetadata(**nb.metadata.kishu)
        metadata.session_count += 1
        nb["metadata"]["kishu"] = asdict(metadata)
        return metadata

    @staticmethod
    def read_kishu_metadata(nb: nbformat.NotebookNode) -> KishuNotebookMetadata:
        if "kishu" not in nb.metadata:
            raise MissingNotebookMetadataError()
        return KishuNotebookMetadata(**nb.metadata.kishu)

    @staticmethod
    def remove_kishu_metadata(nb: nbformat.NotebookNode) -> None:
        if "kishu" not in nb.metadata:
            raise MissingNotebookMetadataError()
        del nb.metadata["kishu"]

    """
    Kishu Jupyter connection information.
    """

    def record_connection(self) -> None:
        with open(KishuPath.connection_path(self._key), 'w') as f:
            f.write(JupyterConnectionInfo(  # type: ignore
                kernel_id=self._kernel_id,
                notebook_path=str(self._path),
            ).to_json())

    @staticmethod
    def try_retrieve_connection(key: str) -> Optional[JupyterConnectionInfo]:
        try:
            with open(KishuPath.connection_path(key), 'r') as f:
                json_str = f.read()
                return JupyterConnectionInfo.from_json(json_str)  # type: ignore
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return None
