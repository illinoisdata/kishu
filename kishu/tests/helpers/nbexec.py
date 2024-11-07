"""
nbexec - Notebook Runner

This module provides a NotebookRunner class for extracting values from cells in a Jupyter notebook.

Classes:
- NotebookRunner: Executes cells in a Jupyter notebook, returns output as a dictionary.

Usage:
1. Create an instance of NotebookRunner, providing the path to the notebook to execute.
2. Use the 'execute' method to specify the cell indices and var_names for the resulting dictionary.
3. 'execute' method runs cells, captures output, and returns result as dictionary.


Dependencies:
- nbconvert: Library for executing Jupyter notebook cells.
- nbformat: Library for working with Jupyter notebook file format.
"""

import os
from typing import Dict, List, Optional, Tuple

import dill
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell

from kishu.jupyter.namespace import Namespace
from kishu.jupyterint import KISHU_VARS

KISHU_INIT_STR: str = "from kishu import init_kishu; init_kishu()"


def get_kishu_checkout_str(cell_num: int, session_num: int = 1, checkout_num: int = 0) -> str:
    return f"_kishu.checkout('{session_num}:{checkout_num}:{cell_num}')"


def get_dump_namespace_str(pickle_file_name: str, var_names: Optional[List[str]] = None) -> str:
    return "\n".join(
        [
            "import dill",
            "dill.dump({k: v for k, v in locals().items() if not k.startswith('_')",
            f"and k not in {Namespace.IPYTHON_VARS.union(KISHU_VARS)}",
            f"and (not {var_names} or k in {var_names})" "},",
            f"open({repr(pickle_file_name)}, 'wb'))",
        ]
    )


class NotebookRunner:
    """
    Executes specified cells in a Jupyter notebook and returns the output as a dictionary.

    Args:
        test_notebook (str): Path to the test notebook to be executed.
    """

    def __init__(self, test_notebook: str):
        """
        Initialize a NotebookRunner instance.

        Args:
            test_notebook (str): Path to the test notebook to be executed.
        """
        self.test_notebook = test_notebook
        self.path_to_notebook = os.path.dirname(self.test_notebook)
        self.pickle_file = test_notebook + ".pickle_file"

    def execute(self, cell_indices: List[int], var_names: Optional[List[str]] = None):
        """
        Executes the specified cells in a Jupyter notebook and returns the output as a dictionary.

        Args:
            cell_indices (List[int]): List of indices of the cells to be executed.

        Returns:
            dict: A dictionary containing the output of the executed cells.
        """
        with open(self.test_notebook) as nb_file:
            notebook = read(nb_file, as_version=4)

        # Create a new notebook object containing only the specified cells
        if cell_indices:
            notebook.cells = [notebook.cells[i] for i in cell_indices]

        # add the dumpsession cell to the notebook
        notebook.cells.append(new_code_cell(source=get_dump_namespace_str(self.pickle_file, var_names)))

        # Execute the notebook cells
        exec_prep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})

        # get the output dictionary
        with open(self.pickle_file, "rb") as file:
            data = dill.load(file)
        return data

    def execute_full_checkout_test(self, cell_num_to_restore: int) -> Tuple[Dict, Dict]:
        """
        Executes the full checkout test by storing the namespace at cell_num_to_restore,
        and namespace after checking out cell_num_to_restore after completely executing the notebook.
        Returns a tuple containing the namespace dict before/after checking out, respectively.

        @param cell_num_to_restore: the cell execution number to restore to.
        """
        # Open the notebook.
        with open(self.test_notebook) as nb_file:
            notebook = read(nb_file, as_version=4)

        # Strip all non-code (e.g., markdown) cells. We won't be needing them.
        notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]

        # The notebook should have at least 2 cells to run this test.
        assert len(notebook["cells"]) >= 2

        # The cell num to restore to should be valid. (the +1 is from the inserted kishu init cell below).
        cell_num_to_restore += 1
        assert cell_num_to_restore >= 2 and cell_num_to_restore <= len(notebook["cells"]) - 1

        # create a kishu initialization cell and add it to the start of the notebook.
        notebook.cells.insert(0, new_code_cell(source=KISHU_INIT_STR))

        # Insert dump session code at middle of notebook after the **cell_num_to_restore**th code cell.
        dumpsession_code_middle = get_dump_namespace_str(self.pickle_file + ".middle")
        notebook.cells.insert(cell_num_to_restore, new_code_cell(source=dumpsession_code_middle))

        # Insert kishu checkout code at end of notebook.
        kishu_checkout_code = get_kishu_checkout_str(cell_num_to_restore)
        notebook.cells.append(new_code_cell(source=kishu_checkout_code))

        # Insert dump session code at end of notebook after kishu checkout.
        dumpsession_code_end = get_dump_namespace_str(self.pickle_file + ".end")
        notebook.cells.append(new_code_cell(source=dumpsession_code_end))

        # Execute the notebook cells.
        exec_prep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})

        # get the output dumped namespace dictionaries.
        data_middle = dill.load(open(self.pickle_file + ".middle", "rb"))
        data_end = dill.load(open(self.pickle_file + ".end", "rb"))

        return data_middle, data_end
