import os
import pathlib


class KishuResource:
    ROOT = pathlib.Path.home()

    @staticmethod
    def kishu_directory() -> str:
        """
        Gets a directory for storing kishu states. Creates if none exists.
        """
        return KishuResource._create_dir(os.path.join(KishuResource.ROOT, ".kishu"))

    @staticmethod
    def notebook_directory(notebook_id: str) -> str:
        """
        Creates a directory kishu will use for checkpointing a notebook. Creates if none exists.
        """
        return KishuResource._create_dir(os.path.join(KishuResource.kishu_directory(), notebook_id))

    @staticmethod
    def checkpoint_path(notebook_id: str) -> str:
        return os.path.join(KishuResource.notebook_directory(notebook_id), "ckpt.sqlite")

    @staticmethod
    def commit_graph_directory(notebook_id: str) -> str:
        return KishuResource._create_dir(os.path.join(
            KishuResource.notebook_directory(notebook_id),
            "commit_graph")
        )

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
