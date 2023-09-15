import json
import os
import shutil
from tempfile import NamedTemporaryFile, gettempdir

import nbformat
from typing import Any
from kishu.checkpoint_io import init_checkpoint_database
from kishu.jupyterint2 import CellExecInfo
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
    exec_info = CellExecInfo()
    exec_info.exec_id = '0:1'
    exec_info.code_block = 'code'
    exec_info.runtime_ms = 2
    exec_info.accessed_resources = ['a']
    exec_info.modified_resources = ['b']
    exec_info.save_into_db(filename)

    log_dict = ExecutionHistory(filename).get_history()
    assert exec_info.exec_id in log_dict

    retrieved_item = log_dict[exec_info.exec_id]
    assert retrieved_item == exec_info


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

    def replace_start_time(exec_info):
        set_field_to(exec_info, 'checkpoint_runtime_ms', 0)
        set_field_to(exec_info, 'end_time_ms', 0)
        set_field_to(exec_info, 'runtime_ms', 0)
        set_field_to(exec_info, 'start_time_ms', 0)
        return exec_info

    history_dict = json.loads(output['history'])
    assert replace_start_time(history_dict['0:1']) == {
            "checkpoint_runtime_ms": 0,
            "code_block": "from kishu import load_kishu\nload_kishu()",
            "end_time_ms": 0,
            "exec_id": "0:1",
            "execution_count": 1
        }
    assert replace_start_time(history_dict['0:2']) == {
            "checkpoint_runtime_ms": 0,
            "checkpoint_vars": ["a"],
            "code_block": "a = 1",
            "end_time_ms": 0,
            "exec_id": "0:2",
            "execution_count": 2,
            "runtime_ms": 0,
            "start_time_ms": 0
        }
