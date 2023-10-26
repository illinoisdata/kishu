import dill
import json
import nbformat
import pytest

from pathlib import Path
from typing import Any, List

from kishu.jupyterint import CommitEntry, KishuForJupyter
from kishu.planning.plan import ExecutionHistory
from kishu.storage.checkpoint_io import init_checkpoint_database

from tests.helpers.nbexec import NotebookRunner


def test_history_to_sqlite(tmp_path: Path):
    # create a temp file for database
    filename = str(tmp_path / "dbfile.sqlite")
    init_checkpoint_database(filename)

    # construct an example
    commit_entry = CommitEntry()
    commit_entry.exec_id = '0:1'
    commit_entry.code_block = 'code'
    commit_entry.runtime_ms = 2
    commit_entry.accessed_resources = ['a']
    commit_entry.modified_resources = ['b']
    commit_entry.save_into_db(filename)

    log_dict = ExecutionHistory(filename).get_history()
    assert commit_entry.exec_id in log_dict

    retrieved_item = log_dict[commit_entry.exec_id]
    assert retrieved_item == commit_entry


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
    def test_checkout(self, tmp_kishu_path_os: Path, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        vals = ['a']
        output = notebook.execute([], vals)
        assert output['a'] == 1

    @pytest.mark.parametrize("set_notebook_path_env", ["test_init_kishu.ipynb"], indirect=True)
    def test_reattatchment(self, tmp_kishu_path_os: Path, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        vals = ['a']
        output = notebook.execute([], vals)
        assert output['a'] == 1

        with open(set_notebook_path_env, "r") as temp_file:
            nb = nbformat.read(temp_file, 4)
            assert nb.metadata.kishu.session_count == 2

    @pytest.mark.parametrize("set_notebook_path_env", ["test_jupyter_load_module.ipynb"], indirect=True)
    def test_record_history(self, tmp_kishu_path_os: Path, set_notebook_path_env):
        notebook = NotebookRunner(set_notebook_path_env)
        exprs = {"history": "repr(_kishu.log())"}
        output = notebook.execute([], [], exprs)

        # The first two cells are something we use for testing. Additional cells appear in the history
        # because of the way NotebookRunner runs.

        def set_field_to(dict_obj: dict, field: str, value: Any):
            if field not in dict_obj:
                return
            dict_obj[field] = value

        def replace_start_time(commit_entry):
            set_field_to(commit_entry, 'checkpoint_runtime_ms', 0)
            set_field_to(commit_entry, 'timestamp_ms', 0)
            set_field_to(commit_entry, 'end_time_ms', 0)
            set_field_to(commit_entry, 'runtime_ms', 0)
            set_field_to(commit_entry, 'start_time_ms', 0)
            set_field_to(commit_entry, 'message', "")
            set_field_to(commit_entry, 'ahg_string', "")
            set_field_to(commit_entry, 'formatted_cells', [])
            set_field_to(commit_entry, 'raw_nb', "")
            set_field_to(commit_entry, 'code_version', 0)
            set_field_to(commit_entry, 'var_version', 0)
            return commit_entry

        # TODO: This test is hacky; we ought to reach for list of commits through public methods.
        history_dict = json.loads(output['history'])
        assert replace_start_time(history_dict['1:1']) == {
                "checkpoint_runtime_ms": 0,
                "code_block": "from kishu import init_kishu\ninit_kishu()\n_kishu.set_test_mode()",
                "end_time_ms": 0,
                "exec_id": "1:1",
                "execution_count": 1,
                'executed_cells': [
                    '',
                    'from kishu import init_kishu\ninit_kishu()\n_kishu.set_test_mode()',
                ],
                "kind": "jupyter",
                "formatted_cells": [],
                "raw_nb": "",
                "message": "",
                "ahg_string": "",
                "code_version": 0,
                "var_version": 0,
                "timestamp_ms": 0,
            }
        assert replace_start_time(history_dict['1:2']) == {
                "checkpoint_runtime_ms": 0,
                "checkpoint_vars": ["a"],
                "code_block": "a = 1",
                "end_time_ms": 0,
                "exec_id": "1:2",
                'executed_cells': [
                    '',
                    'from kishu import init_kishu\ninit_kishu()\n_kishu.set_test_mode()',
                    'a = 1',
                ],
                "execution_count": 2,
                "runtime_ms": 0,
                "start_time_ms": 0,
                "kind": "jupyter",
                "message": "",
                "ahg_string": "",
                "formatted_cells": [],
                "raw_nb": "",
                "code_version": 0,
                "var_version": 0,
                "timestamp_ms": 0,
            }

    @pytest.mark.parametrize(
        ("set_notebook_path_env", "cell_num_to_restore"),
        [
            ('simple.ipynb', 2),
            ('simple.ipynb', 3),
            ('numpy.ipynb', 2),
            ('numpy.ipynb', 3),
            ('numpy.ipynb', 4),
            pytest.param('ml-ex1.ipynb', 10,
                         marks=pytest.mark.skip(reason="Too expensive to run")),
            pytest.param('04_training_linear_models.ipynb', 10,
                         marks=pytest.mark.skip(reason="Too expensive to run")),
            pytest.param('sklearn_tweet_classification.ipynb', 10,
                         marks=pytest.mark.skip(reason="Too expensive to run"))
        ],
        indirect=["set_notebook_path_env"]
    )
    def test_full_checkout(self, tmp_kishu_path_os: Path, set_notebook_path_env, cell_num_to_restore: int):
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
