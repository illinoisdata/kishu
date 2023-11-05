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
import dill
import os
import pickle

from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell
from typing import Dict, List, Tuple

from kishu.jupyterint import IPYTHON_VARS, KISHU_VARS

NB_DIR: str = "tests/notebooks"


# Breaks test_full_checkout in test_jupyterint when using init_kishu
KISHU_LOAD_STR: str = "from kishu import load_kishu; load_kishu(); _kishu.set_test_mode()"
KISHU_INIT_STR: str = "from kishu import init_kishu; init_kishu(); _kishu.set_test_mode()"


def get_kishu_checkout_str(cell_num: int, session_num: int = 0) -> str:
    return f"_kishu.checkout('{session_num}:{cell_num}')"


def get_dump_namespace_str(pickle_file_name: str) -> str:
    return "\n".join(
        [
            "import dill",
            "dill.dump({k: v for k, v in locals().items() if not k.startswith('_')",
            f"and k not in {repr(IPYTHON_VARS.union(KISHU_VARS))}""},",
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
        notebook.cells.insert(0, new_code_cell(source=KISHU_LOAD_STR))

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
        data_middle = dill.load(open(self.pickle_file + '.middle', "rb"))
        data_end = dill.load(open(self.pickle_file + '.end', "rb"))

        return data_middle, data_end
