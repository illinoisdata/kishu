import os

import numpy as np

from kishu.nbexec import NotebookRunner


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


def test_notebookrunner_case_two():
    cell_indices = [i for i in range(27)]
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_2.ipynb"
    objects = ["stable_forest", "stable_loop"]
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, objects)
    expected = {
        "stable_forest": np.array(
            [
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
                [0, 1, 0, 1, 1, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            ]
        ),
        "stable_loop": np.zeros((10, 10)),
    }

    for key in expected.keys():
        assert np.array_equal(output[key], expected[key])


def test_notebookrunner_case_three():
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_3.ipynb"
    objects = ["mse", "intercept"]
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(None, objects)
    expected = {"mse": 0.037113794407976866, "intercept": 0.2525275898181478}

    assert output == expected


def test_notebookrunner_case_four():
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_4.ipynb"
    objects = ["mse", "intercept", "estimated_value"]
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(None, objects)
    expected = {
        "mse": 0.5558915986952442,
        "intercept": -37.02327770606412,
        "estimated_value": -75.30737168169723,
    }

    assert output == expected
