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
    def notebook_directory(notebook_id: str) -> str:
        """
        Creates a directory kishu will use for checkpointing a notebook. Creates if none exists.
        """
        return KishuPath._create_dir(os.path.join(KishuPath.kishu_directory(), notebook_id))

    @staticmethod
    def checkpoint_path(notebook_id: str) -> str:
        return os.path.join(KishuPath.notebook_directory(notebook_id), "ckpt.sqlite")

    @staticmethod
    def commit_graph_directory(notebook_id: str) -> str:
        return KishuPath._create_dir(os.path.join(
            KishuPath.notebook_directory(notebook_id),
            "commit_graph")
        )

    @staticmethod
    def connection_path(notebook_id: str) -> str:
        return os.path.join(KishuPath.notebook_directory(notebook_id), "connection.json")

    @staticmethod
    def head_path(notebook_id: str) -> str:
        return os.path.join(KishuPath.notebook_directory(notebook_id), "head.json")

    @staticmethod
    def iter_notebook_ids() -> Generator[str, None, None]:
        kishu_dir = KishuPath.kishu_directory()
        for notebook_id in os.listdir(KishuPath.kishu_directory()):
            if not os.path.isdir(os.path.join(kishu_dir, notebook_id)):
                continue
            yield notebook_id

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
