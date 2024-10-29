import pytest

from kishu.exceptions import KishuNotInitializedError, NotebookNotFoundError, NotPathError, PathIsNotNotebookError
from kishu.storage.path import KishuPath, NotebookPath

ENV_KISHU_PATH_ROOT = "KISHU_PATH_ROOT"


class TestKishuPath:

    @pytest.fixture
    def kishu_path_root(self, tmp_kishu_path):
        return tmp_kishu_path.ROOT

    def test_kishu_directory(self, kishu_path_root):
        dir_path = KishuPath.kishu_directory()
        assert dir_path == kishu_path_root / ".kishu"
        assert dir_path.exists() and dir_path.is_dir()

    def test_config_path(self, kishu_path_root):
        config_path = KishuPath.config_path()
        assert config_path == kishu_path_root / ".kishu" / "config.ini"

    def test_database_path(self, tmp_path):
        notebook_path = tmp_path / "test_notebook.ipynb"
        notebook_path.touch()
        expected_db_path = tmp_path / "test_notebook.kishudb"
        assert KishuPath.database_path(notebook_path) == expected_db_path

    def test_exists_when_database_exists(self, tmp_path):
        notebook_path = tmp_path / "test_notebook.ipynb"
        notebook_path.touch()
        db_path = tmp_path / "test_notebook.kishudb"
        db_path.touch()
        assert KishuPath.exists(notebook_path) is True

    def test_exists_when_database_does_not_exist(self, tmp_path):
        notebook_path = tmp_path / "test_notebook.ipynb"
        notebook_path.touch()
        assert KishuPath.exists(notebook_path) is False

    def test_create_dir_creates_directory(self, tmp_path):
        new_dir = tmp_path / "new_dir"
        created_dir = KishuPath._create_dir(new_dir)
        assert created_dir == new_dir
        assert new_dir.exists() and new_dir.is_dir()

    def test_create_dir_raises_error_if_path_is_file(self, tmp_path):
        file_path = tmp_path / "file_instead_of_dir"
        file_path.touch()
        with pytest.raises(ValueError, match="Cannot create the directory. Target path is a file."):
            KishuPath._create_dir(file_path)


class TestNotebookPath:

    def test_verify_valid_raises_not_path_error(self):
        with pytest.raises(NotPathError):
            NotebookPath.verify_valid("not_a_path_object")

    def test_verify_valid_raises_notebook_not_found_error(self, tmp_path):
        nonexistent_notebook = tmp_path / "nonexistent_notebook.ipynb"
        with pytest.raises(NotebookNotFoundError):
            NotebookPath.verify_valid(nonexistent_notebook)

    def test_verify_valid_raises_path_is_not_notebook_error(self, tmp_path):
        invalid_notebook_path = tmp_path / "not_a_notebook.txt"
        invalid_notebook_path.touch()
        with pytest.raises(PathIsNotNotebookError):
            NotebookPath.verify_valid(invalid_notebook_path)

    def test_verify_valid_passes_for_valid_notebook_path(self, tmp_path):
        valid_notebook_path = tmp_path / "test_notebook.ipynb"
        valid_notebook_path.touch()
        # No exception should be raised
        NotebookPath.verify_valid(valid_notebook_path)

    def test_verify_valid_and_initialized_raises_kishu_not_initialized_error(self, tmp_path):
        notebook_path = tmp_path / "test_notebook.ipynb"
        notebook_path.touch()
        with pytest.raises(KishuNotInitializedError):
            NotebookPath.verify_valid_and_initialized(notebook_path)

    def test_verify_valid_and_initialized_passes_when_initialized(self, tmp_path):
        notebook_path = tmp_path / "test_notebook.ipynb"
        notebook_path.touch()
        db_path = tmp_path / "test_notebook.kishudb"
        db_path.touch()
        # No exception should be raised
        NotebookPath.verify_valid_and_initialized(notebook_path)
