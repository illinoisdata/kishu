import dill
import json
import nbformat
import os
import pytest
import shutil

from pathlib import Path
from typing import Any

from kishu.jupyterint import CommitEntry
from kishu.planning.plan import ExecutionHistory
from kishu.storage.checkpoint_io import init_checkpoint_database

from tests.helpers.nbexec import NB_DIR, NotebookRunner


def create_temporary_copy(path: str, filename: str, temp_dir: str):
    temp_path = os.path.join(temp_dir, filename)
    shutil.copy2(path, temp_path)
    return temp_path


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


def test_checkout(tmp_kishu_path_os: Path):
    path_to_notebook = os.getcwd()
    notebook_name = "test_jupyter_checkout.ipynb"
    vals = ['a']
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
    output = notebook.execute([], vals)
    assert output['a'] == 1


def test_reattatchment(tmp_kishu_path_os: Path, tmp_path):
    path_to_notebook = os.getcwd()
    notebook_name = "test_init_kishu.ipynb"
    notebook_full_path = os.path.join(path_to_notebook, NB_DIR, notebook_name)
    temp_path = create_temporary_copy(notebook_full_path, notebook_name, tmp_path)
    vals = ['a']
    notebook = NotebookRunner(temp_path)
    output = notebook.execute([], vals)
    assert output['a'] == 1
    with open(temp_path, "r") as temp_file:
        nb = nbformat.read(temp_file, 4)
        assert nb.metadata.kishu.session_count == 2


def test_record_history(tmp_kishu_path_os: Path):
    path_to_notebook = os.getcwd()
    notebook_name = "test_jupyter_load_module.ipynb"
    exprs = {"history": "repr(_kishu.log())"}
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
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
        set_field_to(commit_entry, 'code_version', 0)
        set_field_to(commit_entry, 'var_version', 0)
        return commit_entry

    # TODO: This test is hacky; we ought to reach for list of commits through public methods.
    history_dict = json.loads(output['history'])
    assert replace_start_time(history_dict['0:1']) == {
            "checkpoint_runtime_ms": 0,
            "code_block": "from kishu import load_kishu\nload_kishu()\n_kishu.set_test_mode()",
            "end_time_ms": 0,
            "exec_id": "0:1",
            "execution_count": 1,
            'executed_cells': [
                '',
                'from kishu import load_kishu\nload_kishu()\n_kishu.set_test_mode()',
            ],
            "kind": "jupyter",
            "message": "",
            "ahg_string": "",
            "code_version": 0,
            "var_version": 0,
            "timestamp_ms": 0,
        }
    assert replace_start_time(history_dict['0:2']) == {
            "checkpoint_runtime_ms": 0,
            "checkpoint_vars": ["a"],
            "code_block": "a = 1",
            "end_time_ms": 0,
            "exec_id": "0:2",
            'executed_cells': [
                '',
                'from kishu import load_kishu\nload_kishu()\n_kishu.set_test_mode()',
                'a = 1',
            ],
            "execution_count": 2,
            "runtime_ms": 0,
            "start_time_ms": 0,
            "kind": "jupyter",
            "message": "",
            "ahg_string": "",
            "code_version": 0,
            "var_version": 0,
            "timestamp_ms": 0,
        }


@pytest.mark.parametrize(("notebook_name", "cell_num_to_restore"), [
        ('simple.ipynb', 2),
        ('simple.ipynb', 3),
        ('numpy.ipynb', 2),
        ('numpy.ipynb', 3),
        ('numpy.ipynb', 4),
        pytest.param('ml-ex1.ipynb', 10, marks=pytest.mark.skip(reason="Too expensive to run")),
        pytest.param('04_training_linear_models.ipynb', 10, marks=pytest.mark.skip(reason="Too expensive to run")),
        pytest.param('sklearn_tweet_classification.ipynb', 10, marks=pytest.mark.skip(reason="Too expensive to run"))]
    )
def test_full_checkout(tmp_kishu_path_os: Path, notebook_name: str, cell_num_to_restore: int):
    """
        Tests checkout correctness by comparing namespace contents at cell_num_to_restore in the middle of a notebook,
        and namespace contents after checking out cell_num_to_restore completely executing the notebook.

        @param notebook_name: input notebook name.
        @param cell_num_to_restore: the cell execution number to restore to.
    """
    # Open notebook.
    path_to_notebook = os.getcwd()
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))

    # Get notebook namespace contents at cell execution X and contents after checking out cell execution X.
    namespace_before_checkout, namespace_after_checkout = notebook.execute_full_checkout_test(cell_num_to_restore)

    # The contents should be identical.
    assert namespace_before_checkout.keys() == namespace_after_checkout.keys()
    for key in namespace_before_checkout.keys():
        # As certain classes don't have equality (__eq__) implemented, we compare serialized bytestrings.
        assert dill.dumps(namespace_before_checkout[key]) == dill.dumps(namespace_after_checkout[key])
