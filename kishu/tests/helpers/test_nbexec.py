import pytest

import os
import numpy as np

from tests.helpers.nbexec import NB_DIR, NotebookRunner


def test_notebookrunner_basic():
    cell_indices = [0, 1, 2]
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_1.ipynb"
    objects = ["z", "b", "a"]
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
    output = notebook.execute(cell_indices, objects)
    assert output == {"z": 2, "b": 9, "a": 1}


def test_notebookrunner_no_cells():
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_1.ipynb"
    objects = ["a", "b", "x", "y", "z"]
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
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
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
    output = notebook.execute(cell_indices, objects)
    assert output == {
        "a": 1,
        "b": 9,
        "x": 23,
        "y": "Hello World!",
        "z": [1, 2, 3, 4, 5],
    }


@pytest.mark.skip(reason="Too expensive to run (~21s)")
def test_notebookrunner_case_two():
    cell_indices = [i for i in range(27)]
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_2.ipynb"
    objects = ["stable_forest", "stable_loop"]
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
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


@pytest.mark.skip(reason="Too expensive to run (~3s)")
def test_notebookrunner_case_three():
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_3.ipynb"
    objects = ["mse", "intercept"]
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
    output = notebook.execute(None, objects)
    expected = {"mse": 0.04, "intercept": 0.25}

    assert output == expected


def test_notebookrunner_case_four():
    path_to_notebook = os.getcwd()
    notebook_name = "nbexec_test_case_4.ipynb"
    objects = ["mse", "intercept", "estimated_value"]
    notebook = NotebookRunner(os.path.join(path_to_notebook, NB_DIR, notebook_name))
    output = notebook.execute(None, objects)
    expected = {
        "mse": 0.56,
        "intercept": -37.02,
        "estimated_value": -75.31,
    }

    assert output == expected
