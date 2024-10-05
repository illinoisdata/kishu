import os
import pathlib
from typing import Generator

ENV_KISHU_PATH_ROOT = "KISHU_PATH_ROOT"


class KishuPath:
    ROOT = os.environ.get(ENV_KISHU_PATH_ROOT, None) or str(pathlib.Path.home())

    @staticmethod
    def kishu_directory() -> str:
        """
        Gets a directory for storing kishu states. Creates if none exists.
        """
        return KishuPath._create_dir(os.path.join(KishuPath.ROOT, ".kishu"))

    @staticmethod
    def notebook_directory(notebook_key: str) -> str:
        """
        Creates a directory kishu will use for checkpointing a notebook. Creates if none exists.
        """
        return KishuPath._create_dir(os.path.join(KishuPath.kishu_directory(), notebook_key))

    @staticmethod
    def database_path(notebook_key: str) -> str:
        return os.path.join(KishuPath.notebook_directory(notebook_key), "ckpt.sqlite")

    @staticmethod
    def commit_graph_directory(notebook_key: str) -> str:
        return KishuPath._create_dir(os.path.join(KishuPath.notebook_directory(notebook_key), "commit_graph"))

    @staticmethod
    def nb_commit_graph_directory(notebook_key: str) -> str:
        return KishuPath._create_dir(os.path.join(KishuPath.notebook_directory(notebook_key), "nb_commit_graph"))

    @staticmethod
    def connection_path(notebook_key: str) -> str:
        return os.path.join(KishuPath.notebook_directory(notebook_key), "connection.json")

    @staticmethod
    def head_path(notebook_key: str) -> str:
        return os.path.join(KishuPath.notebook_directory(notebook_key), "head.json")

    @staticmethod
    def exists(notebook_key: str) -> bool:
        return os.path.exists(os.path.join(KishuPath.kishu_directory(), notebook_key))

    @staticmethod
    def iter_notebook_keys() -> Generator[str, None, None]:
        kishu_dir = KishuPath.kishu_directory()
        for notebook_key in os.listdir(KishuPath.kishu_directory()):
            if not os.path.isdir(os.path.join(kishu_dir, notebook_key)):
                continue
            yield notebook_key

    @staticmethod
    def _create_dir(dir: str) -> str:
        """
        Creates a new directory if not exists.

        @param dir  A directory to create.
        @return  Echos the newly created directory.
        """
        if os.path.isfile(dir):
            raise ValueError("The passed directory name exists as s file.")
        if not os.path.exists(dir):
            os.mkdir(dir)
        return dir
