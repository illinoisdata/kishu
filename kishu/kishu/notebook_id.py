from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import nbformat
from dataclasses_json import dataclass_json

from kishu.exceptions import MissingNotebookMetadataError, NotNotebookPathOrKey
from kishu.jupyter.runtime import JupyterRuntimeEnv
from kishu.storage.path import KishuPath


@dataclass
class KishuNotebookMetadata:
    notebook_id: str
    session_count: int = 1


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
    def from_enclosing(path: Optional[Path]) -> NotebookId:
        kernel_id = JupyterRuntimeEnv.enclosing_kernel_id()
        path = path or JupyterRuntimeEnv.notebook_path_from_kernel(kernel_id)

        # Retrieve key if any, otherwise create new key.
        try:
            nb = JupyterRuntimeEnv.read_notebook(path)
            metadata = NotebookId.read_kishu_metadata(nb)
            key = metadata.notebook_id
        except MissingNotebookMetadataError:
            key = datetime.now().strftime("%Y%m%dT%H%M%S")

        return NotebookId(key=key, path=path, kernel_id=kernel_id)

    @staticmethod
    def parse_key_from_path(path: Path) -> str:
        nb = JupyterRuntimeEnv.read_notebook(path)
        metadata = NotebookId.read_kishu_metadata(nb)
        return metadata.notebook_id

    @staticmethod
    def verify_metadata_exists(path: Path) -> bool:
        nb = JupyterRuntimeEnv.read_notebook(path)
        try:
            NotebookId.read_kishu_metadata(nb)
            return True
        except MissingNotebookMetadataError:
            return False

    @staticmethod
    def parse_key_from_path_or_key(path_or_key: str) -> str:
        # Try parsing as path, if exists.
        path = Path(path_or_key)
        if path.exists():
            try:
                return NotebookId.parse_key_from_path(path)
            except (nbformat.reader.NotJSONError, UnicodeDecodeError):
                # Ignore non-notebook file.
                pass

        # Notebook path does not exist, try parsing as key.
        key = path_or_key
        if KishuPath.exists(key):
            return key

        raise NotNotebookPathOrKey(path_or_key)

    @staticmethod
    def parse_path_from_path_or_key(path_or_key: str) -> Path:
        # Try parsing as path
        path = Path(path_or_key)
        if path.exists():
            try:
                JupyterRuntimeEnv.read_notebook(path)
                return path
            except (nbformat.reader.NotJSONError, UnicodeDecodeError):
                # Ignore non-notebook file.
                pass

        # Not a path, try parsing as key.
        key = path_or_key
        if KishuPath.exists(key):
            conn_info = NotebookId.try_retrieve_connection(key)
            if conn_info:
                return Path(conn_info.notebook_path)
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

    def create_kishu_metadata(self, nb: nbformat.NotebookNode) -> KishuNotebookMetadata:
        metadata = KishuNotebookMetadata(self.key())
        if "kishu" in nb.metadata:
            assert nb.metadata["kishu"]["notebook_id"] == self.key()
            metadata.session_count = nb.metadata["kishu"]["session_count"] + 1
        return metadata

    @staticmethod
    def read_kishu_metadata(nb: nbformat.NotebookNode) -> KishuNotebookMetadata:
        if "kishu" not in nb.metadata:
            raise MissingNotebookMetadataError()
        return KishuNotebookMetadata(**nb.metadata.kishu)

    @staticmethod
    def add_kishu_metadata(nb: nbformat.NotebookNode, metadata: KishuNotebookMetadata) -> None:
        nb.metadata["kishu"] = asdict(metadata)

    @staticmethod
    def remove_kishu_metadata(nb: nbformat.NotebookNode) -> None:
        if "kishu" not in nb.metadata:
            raise MissingNotebookMetadataError()
        del nb.metadata["kishu"]

    """
    Kishu Jupyter connection information.
    """

    def record_connection(self) -> None:
        with open(KishuPath.connection_path(self._key), "w") as f:
            f.write(
                JupyterConnectionInfo(  # type: ignore
                    kernel_id=self._kernel_id,
                    notebook_path=str(self._path),
                ).to_json()
            )

    @staticmethod
    def try_retrieve_connection(key: str) -> Optional[JupyterConnectionInfo]:
        try:
            with open(KishuPath.connection_path(key), "r") as f:
                json_str = f.read()
                return JupyterConnectionInfo.from_json(json_str)  # type: ignore
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return None
