import os

from nbexec import NotebookRunner


def test_notebookrunner_basic():
    cell_indices = [0, 1, 2]
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_1.ipynb"
    objects = ["z", "b", "a"]
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, objects)
    assert output == {"z": 2, "b": 9, "a": 1}


def test_notebookrunner_no_cells():
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_1.ipynb"
    objects = ["a", "b", "x", "y", "z"]
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(None, objects)
    assert output == {
        "a": 1,
        "b": 9,
        "x": 23,
        "y": "Hello World!",
        "z": [1, 2, 3, 4, 5],
    }


def test_notebookrunner_empty_cell_list():
    cell_indices = []
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_1.ipynb"
    objects = ["a", "b", "x", "y", "z"]
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, objects)
    assert output == {
        "a": 1,
        "b": 9,
        "x": 23,
        "y": "Hello World!",
        "z": [1, 2, 3, 4, 5],
    }
