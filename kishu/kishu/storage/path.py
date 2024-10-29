import os
from pathlib import Path

from kishu.exceptions import KishuNotInitializedError, NotebookNotFoundError, NotPathError, PathIsNotNotebookError

ENV_KISHU_PATH_ROOT = "KISHU_PATH_ROOT"


class KishuPath:
    ROOT = Path(os.environ.get(ENV_KISHU_PATH_ROOT, str(Path.home())))

    @staticmethod
    def kishu_directory() -> Path:
        """
        Gets a directory for storing kishu states. Creates if none exists.
        """
        return KishuPath._create_dir(KishuPath.ROOT / ".kishu")

    @staticmethod
    def config_path() -> Path:
        """
        Gets path to Kishu configuration file.
        """
        return KishuPath.kishu_directory() / "config.ini"

    @staticmethod
    def database_path(notebook_path: Path) -> Path:
        """
        Gets database path for the notebook.
        """
        notebook_name = notebook_path.resolve().stem
        return notebook_path.resolve().parent / f"{notebook_name}.kishudb"

    @staticmethod
    def exists(notebook_path: Path) -> bool:
        """
        Checks whether Kishu database for the given notebook exists.
        """
        return KishuPath.database_path(notebook_path).exists()

    @staticmethod
    def _create_dir(dir_path: Path) -> Path:
        """
        Creates a new directory if not exists.

        @param   dir_path  A directory to create.
        @return  Echos the newly created directory.
        """
        if dir_path.is_file():
            raise ValueError("Cannot create the directory. Target path is a file.")
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path


class NotebookPath(Path):

    @staticmethod
    def verify_valid(notebook_path: Path):
        if not isinstance(notebook_path, Path):
            raise NotPathError(notebook_path)
        if not notebook_path.exists():
            raise NotebookNotFoundError(notebook_path)
        if notebook_path.suffix != ".ipynb":
            raise PathIsNotNotebookError(notebook_path)

    @staticmethod
    def verify_valid_and_initialized(notebook_path: Path):
        NotebookPath.verify_valid(notebook_path)
        if not KishuPath.exists(notebook_path):
            raise KishuNotInitializedError(notebook_path)
