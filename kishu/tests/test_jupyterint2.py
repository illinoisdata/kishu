import json
import os
import shutil
from tempfile import NamedTemporaryFile, gettempdir

import nbformat
from typing import Any
from kishu.checkpoint_io import init_checkpoint_database
from kishu.jupyterint2 import CommitEntry
from kishu.nbexec import NotebookRunner
from kishu.plan import ExecutionHistory


def create_temporary_copy(path, filename):
    temp_dir = gettempdir()
    temp_path = os.path.join(temp_dir, filename)
    shutil.copy2(path, temp_path)
    return temp_path


def test_history_to_sqlite():
    # create a temp file for database
    _checkpoint_file = NamedTemporaryFile()
    filename = _checkpoint_file.name
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


def test_checkout():
    cell_indices = []
    path_to_notebook = os.getcwd()
    notebook_name = "test_jupyter_checkout.ipynb"
    vals = ['a']
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, vals)
    assert output['a'] == 1


def test_reattatchment():
    cell_indices = []
    path_to_notebook = os.getcwd()
    notebook_name = "test_init_kishu.ipynb"
    notebook_full_path = path_to_notebook + "/tests/" + notebook_name
    temp_path = create_temporary_copy(notebook_full_path, notebook_name)
    vals = ['a']
    notebook = NotebookRunner(temp_path)
    output = notebook.execute(cell_indices, vals)
    assert output['a'] == 1
    with open(temp_path, "r") as temp_file:
        nb = nbformat.read(temp_file, 4)
        assert nb.metadata.kishu.session_count == 2


def test_record_history():
    cell_indices = []
    path_to_notebook = os.getcwd()
    notebook_name = "test_jupyter_load_module.ipynb"
    exprs = {"history": "repr(_kishu.log())"}
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, [], exprs)

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
        return commit_entry

    # TODO: This test is hacky; we ought to reach for list of commits through public methods.
    history_dict = json.loads(output['history'])
    assert replace_start_time(history_dict['0:1']) == {
            "checkpoint_runtime_ms": 0,
            "code_block": "from kishu import load_kishu\nload_kishu()\n_kishu.set_test_mode()",
            "end_time_ms": 0,
            "exec_id": "0:1",
            "execution_count": 1,
            "kind": "jupyter",
            "message": "",
            "ahg_string": "",
            "timestamp_ms": 0,
        }
    assert replace_start_time(history_dict['0:2']) == {
            "checkpoint_runtime_ms": 0,
            "checkpoint_vars": ["a"],
            "code_block": "a = 1",
            "end_time_ms": 0,
            "exec_id": "0:2",
            "execution_count": 2,
            "runtime_ms": 0,
            "start_time_ms": 0,
            "kind": "jupyter",
            "message": "",
            "ahg_string": "",
            "timestamp_ms": 0,
        }
