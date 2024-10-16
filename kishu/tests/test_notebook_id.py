from pathlib import Path

from kishu.notebook_id import NotebookId


class TestNotebookId:
    def test_from_enclosing_with_key(self, notebook_key, set_notebook_path_env):
        notebook_id = NotebookId.from_enclosing_with_key(notebook_key)
        assert notebook_id.key() == notebook_key
        assert notebook_id.path() == Path(set_notebook_path_env)
        assert notebook_id.kernel_id() == "test_kernel_id"
