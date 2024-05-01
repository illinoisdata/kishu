import nbformat
import pytest

from typing import List

from kishu.jupyterint import KishuForJupyter

from tests.helpers.nbexec import NotebookRunner


class TestOnMockEnclosing:
    def test_disambiguate_commit_pass(
        self,
        kishu_jupyter: KishuForJupyter,
        notebook_key: str,
        basic_execution_ids: List[str],
    ) -> None:
        commit_ids = basic_execution_ids
        assert KishuForJupyter.disambiguate_commit(notebook_key, commit_ids[0]) == commit_ids[0]
        assert KishuForJupyter.disambiguate_commit(notebook_key, commit_ids[1]) == commit_ids[1]
        assert KishuForJupyter.disambiguate_commit(notebook_key, commit_ids[2]) == commit_ids[2]

    def test_disambiguate_commit_not_exist(
        self,
        kishu_jupyter: KishuForJupyter,
        notebook_key: str,
        basic_execution_ids: List[str],
    ) -> None:
        with pytest.raises(ValueError):
            _ = KishuForJupyter.disambiguate_commit(notebook_key, "NON_EXISTENT_COMMIT_ID")

    def test_disambiguate_commit_ambiguous(
        self,
        kishu_jupyter: KishuForJupyter,
        notebook_key: str,
        basic_execution_ids: List[str],
    ) -> None:
        commit_ids = basic_execution_ids
        common_prefix = commit_ids[0][:1]
        assert sum(common_prefix in commit_id for commit_id in commit_ids) > 1, f"No common prefix {commit_ids}"
        with pytest.raises(ValueError):
            _ = KishuForJupyter.disambiguate_commit(notebook_key, common_prefix)


class TestOnNotebookRunner:

    # Modify the test_checkout to use the new fixture.
    @pytest.mark.parametrize("set_notebook_path_env", ["test_jupyter_checkout.ipynb"], indirect=True)
    def test_checkout(self, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        output = notebook.execute([])
        assert output['a'] == 1

    @pytest.mark.parametrize("set_notebook_path_env", ["test_init_kishu.ipynb"], indirect=True)
    def test_reattatchment(self, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        output = notebook.execute([])
        assert output['a'] == 1

        with open(set_notebook_path_env, "r") as temp_file:
            nb = nbformat.read(temp_file, 4)
            assert nb.metadata.kishu.session_count == 2

    @pytest.mark.parametrize("set_notebook_path_env", ["test_detach_kishu.ipynb"], indirect=True)
    def test_detachment_valid(self, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        notebook.execute([])
        with open(set_notebook_path_env, "r") as nb_file:
            nb = nbformat.read(nb_file, 4)
            assert "kishu" not in nb.metadata

    @pytest.mark.parametrize("set_notebook_path_env", ["test_detach_kishu_no_init.ipynb"], indirect=True)
    def test_detachment_fails_gracefully(self, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        notebook.execute([])
        assert True  # making sure no errors were thrown
