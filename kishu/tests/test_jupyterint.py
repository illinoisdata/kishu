from pathlib import Path
from typing import List

import dill
import nbformat
import pytest

from kishu.jupyterint import KishuForJupyter
from kishu.storage.commit import KishuCommit, NotebookCommitState
from tests.helpers.nbexec import NotebookRunner


class TestOnMockEnclosing:
    def test_disambiguate_commit_pass(
        self,
        kishu_jupyter: KishuForJupyter,
        basic_notebook_path: Path,
        basic_execution_ids: List[str],
    ) -> None:
        commit_ids = basic_execution_ids
        assert KishuForJupyter.disambiguate_commit(basic_notebook_path, commit_ids[0]) == commit_ids[0]
        assert KishuForJupyter.disambiguate_commit(basic_notebook_path, commit_ids[1]) == commit_ids[1]
        assert KishuForJupyter.disambiguate_commit(basic_notebook_path, commit_ids[2]) == commit_ids[2]

    def test_disambiguate_commit_not_exist(
        self,
        kishu_jupyter: KishuForJupyter,
        basic_notebook_path: Path,
        basic_execution_ids: List[str],
    ) -> None:
        with pytest.raises(ValueError):
            _ = KishuForJupyter.disambiguate_commit(basic_notebook_path, "NON_EXISTENT_COMMIT_ID")

    def test_disambiguate_commit_ambiguous(
        self,
        kishu_jupyter: KishuForJupyter,
        basic_notebook_path: Path,
        basic_execution_ids: List[str],
    ) -> None:
        commit_ids = basic_execution_ids
        common_prefix = commit_ids[0][:1]
        assert sum(common_prefix in commit_id for commit_id in commit_ids) > 1, f"No common prefix {commit_ids}"
        with pytest.raises(ValueError):
            _ = KishuForJupyter.disambiguate_commit(basic_notebook_path, common_prefix)

    def test_amend_notebook(
        self, kishu_jupyter: KishuForJupyter, notebook_key: str, basic_execution_ids: List[str], set_notebook_path_env
    ):
        # Check notebook record type is "with_commit" before updating.
        latest_commit_id = basic_execution_ids[-1]
        kishu_commit = KishuCommit(kishu_jupyter.database_path())
        pre_latest_entry = kishu_commit.get_commit(latest_commit_id)
        assert pre_latest_entry.nb_record_type == NotebookCommitState.with_commit

        kishu_jupyter.amend_notebook()

        # Now the type should be "latest".
        post_latest_entry = kishu_commit.get_commit(latest_commit_id)
        assert post_latest_entry.nb_record_type == NotebookCommitState.amend_notebook


class TestOnNotebookRunner:

    # Modify the test_checkout to use the new fixture.
    @pytest.mark.parametrize("set_notebook_path_env", ["test_jupyter_checkout.ipynb"], indirect=True)
    def test_checkout(self, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        output = notebook.execute([])
        assert output["a"] == 1

    @pytest.mark.parametrize("set_notebook_path_env", ["test_init_kishu.ipynb"], indirect=True)
    def test_reattatchment(self, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        output = notebook.execute([])
        assert output["a"] == 1

        with open(set_notebook_path_env, "r") as temp_file:
            nb = nbformat.read(temp_file, 4)
            assert nb.metadata.kishu.session_count == 2

    @pytest.mark.parametrize(
        ("set_notebook_path_env", "cell_num_to_restore"),
        [
            ("simple.ipynb", 2),
            ("simple.ipynb", 3),
            ("numpy.ipynb", 2),
            ("numpy.ipynb", 3),
            ("numpy.ipynb", 4),
            pytest.param("ml-ex1.ipynb", 10, marks=pytest.mark.skip(reason="Too expensive to run")),
            pytest.param("04_training_linear_models.ipynb", 10, marks=pytest.mark.skip(reason="Too expensive to run")),
            pytest.param("sklearn_tweet_classification.ipynb", 10, marks=pytest.mark.skip(reason="Too expensive to run")),
        ],
        indirect=["set_notebook_path_env"],
    )
    def test_full_checkout(self, set_notebook_path_env, cell_num_to_restore: int):
        """
        Tests checkout correctness by comparing namespace contents at cell_num_to_restore in the middle of a notebook,
        and namespace contents after checking out cell_num_to_restore completely executing the notebook.
        """
        notebook = NotebookRunner(set_notebook_path_env)

        # Get notebook namespace contents at cell execution X and contents after checking out cell execution X.
        namespace_before_checkout, namespace_after_checkout = notebook.execute_full_checkout_test(cell_num_to_restore)

        # The contents should be identical.
        assert namespace_before_checkout.keys() == namespace_after_checkout.keys()
        for key in namespace_before_checkout.keys():
            # As certain classes don't have equality (__eq__) implemented, we compare serialized bytestrings.
            assert dill.dumps(namespace_before_checkout[key]) == dill.dumps(namespace_after_checkout[key])

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
