import json
import os

from kishu.nbexec import NotebookRunner


def test_record_history():
    cell_indices = []
    path_to_notebook = os.getcwd()
    notebook_name = "jupyterint_test.ipynb"
    exprs = {"history": "repr(history)"}
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, [], exprs)

    # The first two cells are something we use for testing. Additional cells appear in the history
    # because of the way NotebookRunner runs.

    def replace_start_time(exec_info):
        if exec_info['start_time_ms'] is not None:
            exec_info['start_time_ms'] = 0
        return exec_info

    first_two_items = json.loads(output['history'])[:2]
    assert [replace_start_time(item) for item in first_two_items] == [
        {
            "accessed_resources": [],
            "code_block": "from kishu import register_kishu\nhistory = register_kishu(get_ipython())",
            "error_before_exec": None,
            "error_in_exec": None,
            "execution_count": 1,
            "modified_resources": [],
            "result": None,
            "runtime_ms": None,
            "start_time_ms": None
        },
        {
            "accessed_resources": [],
            "code_block": "a = 1",
            "error_before_exec": None,
            "error_in_exec": None,
            "execution_count": 2,
            "modified_resources": [],
            "result": None,
            "runtime_ms": None,
            "start_time_ms": 0
        }
    ]
