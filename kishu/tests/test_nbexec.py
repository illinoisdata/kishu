import os

from nbexec import NotebookRunner


def test_notebookrunner_basic():
    cell_indices = [0, 1, 2, 3]
    path_to_notebook = os.getcwd()
    notebook_name = "test_basic.ipynb"
    objects = ["z", "b", "a"]
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, objects)
    assert output == {"z": 2, "b": 9, "a": 1}
