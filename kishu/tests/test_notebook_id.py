import pytest

from pathlib import Path

from kishu.exceptions import MissingNotebookMetadataError, NotNotebookPathOrKey
from kishu.notebook_id import NotebookId


class TestNotebookId:
    def test_from_enclosing_with_key(self, notebook_key, set_notebook_path_env):
        notebook_id = NotebookId.from_enclosing_with_key(notebook_key)
        assert notebook_id.key() == notebook_key
        assert notebook_id.path() == Path(set_notebook_path_env)
        assert notebook_id.kernel_id() == "test_kernel_id"

    def test_parse_key_from_path_without_kishu(self, set_notebook_path_env):
        with pytest.raises(MissingNotebookMetadataError):
            _ = NotebookId.parse_key_from_path_or_key(set_notebook_path_env)

    @pytest.mark.parametrize("set_notebook_path_env", ["simple_with_kishu.ipynb"], indirect=True)
    def test_parse_key_from_path(self, set_notebook_path_env):
        notebook_key = NotebookId.parse_key_from_path_or_key(set_notebook_path_env)
        assert notebook_key == "simple_kishu_notebook_key"  # From notebook metadata.

    def test_parse_key_from_key(self, kishu_jupyter, notebook_key):
        notebook_key = NotebookId.parse_key_from_path_or_key(notebook_key)
        assert notebook_key == notebook_key

    def test_parse_key_neither(self):
        with pytest.raises(NotNotebookPathOrKey):
            _ = NotebookId.parse_key_from_path_or_key("non_existent_notebook.ipynb")
