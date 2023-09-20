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
import pickle
from typing import List, Dict

from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell


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
        self.pickle_file = "/tmp/pickle_" + os.path.basename(self.test_notebook)

    def execute(self, cell_indices: List[int], var_names: List[str], eval_expr: Dict[str, str] = {}):
        """
        Executes the specified cells in a Jupyter notebook and returns the output as a dictionary.

        Args:
            cell_indices (List[int]): List of indices of the cells to be executed.
            var_names (List[str]): List of var_names to include in the resulting dictionary.
            eval_expr (Dict[str, str]): Map from names to expressions to evaluate.

        Returns:
            dict: A dictionary containing the output of the executed cells.
        """
        with open(self.test_notebook) as nb_file:
            notebook = read(nb_file, as_version=4)

        # Create a new notebook object containing only the specified cells
        if cell_indices is None or not cell_indices:
            new_nb = notebook
        else:
            new_nb = notebook.copy()
            new_nb.cells = [notebook.cells[i] for i in cell_indices]

        # Make dictionary and then pickle that into a file
        code = "\n".join(
            [
                "import pickle",
                "my_list = {}".format(var_names),
                "my_dict = {}".format(eval_expr),
                "fout = open('{}', 'wb')".format(self.pickle_file),
            ]
        )
        code_two = "\n".join(
            [
                "test = locals()",
                "print(test)",
                "result_dict = {}",
                "result_dict.update({var: test[var] for var in my_list})",
                "result_dict.update({name: eval(expr) for name, expr in my_dict.items()})",
                "pickle.dump(result_dict, fout)",
                "print(result_dict)",
                "fout.close()",
            ]
        )

        # create a new code cell
        new_cell = new_code_cell(source=code)
        new_cell_two = new_code_cell(source=code_two)

        # add the new cell to the notebook
        new_nb.cells.append(new_cell)
        new_nb.cells.append(new_cell_two)

        # Execute the notebook cells
        exec_prep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        exec_prep.preprocess(new_nb, {"metadata": {"path": self.path_to_notebook}})

        # get the output dictionary
        with open(self.pickle_file, "rb") as file:
            data = pickle.load(file)
        return data
