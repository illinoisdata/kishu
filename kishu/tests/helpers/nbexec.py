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
import time
from IPython.core.interactiveshell import InteractiveShell

from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell
from typing import Dict, List, Optional, Tuple

from kishu.jupyter.namespace import Namespace
from kishu.jupyterint import KISHU_VARS

KISHU_INIT_STR: str = "from kishu import init_kishu; init_kishu();"


def get_kishu_checkout_str(cell_num: int, session_num: int = 1) -> str:
    return f"_kishu.checkout('{session_num}:{cell_num}')"


def get_criu_store_str(notebook_name, filename, cell_num, pid) -> str:
    return "\n".join(
        [
            "req = rpc.criu_req()",
            "req.type = rpc.DUMP",
            "req.opts.leave_running = True",
            "req.opts.shell_job = True",
            "req.opts.log_level = 4",
            f"directory = '/data/elastic-notebook/criu/{notebook_name}_False_{cell_num}'",
            "if not os.path.exists(directory):",
            "    os.makedirs(directory)",
            "req.opts.images_dir_fd = os.open(directory, os.O_DIRECTORY)",
            "s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)",
            "s.connect('/data/elastic-notebook/criu-rpc')",
            "s.send(req.SerializeToString())",
            "start = time.time()",
            "data = s.recv(2048)",
            "end = time.time() - start",
            "end_format = '{:.8f}'.format(end)",
            "filesize = sum(f.stat().st_size for f in Path(directory).glob('**/*') if f.is_file())",
            f"with open('{filename}', 'a', newline='') as results_file:",
            f"    half_str = 'criu_incremental_False,{notebook_name},{cell_num}'",
            """    results_file.write(half_str + ',checkpoint-time,' + end_format + '\\n')""",
            """    results_file.write(half_str + ',checkpoint-size,' + str(filesize) + '\\n')""",
        ]
    )


def get_criu_store_incremental_str(notebook_name, filename, cell_num, pid) -> str:
    return "\n".join(
        [
            "req = rpc.criu_req()",
            "req.type = rpc.DUMP",
            "req.opts.leave_running = True",
            "req.opts.shell_job = True",
            "req.opts.log_level = 4",
            "req.opts.track_mem = True",
            f"if {cell_num} > 0:",
            f"    req.opts.parent_img = '/data/elastic-notebook/criu/{notebook_name}_True_{cell_num - 1}'",
            f"directory = '/data/elastic-notebook/criu/{notebook_name}_True_{cell_num}'",
            "if not os.path.exists(directory):",
            "    os.makedirs(directory)",
            "req.opts.images_dir_fd = os.open(directory, os.O_DIRECTORY)",
            "s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)",
            "s.connect('/data/elastic-notebook/criu-rpc')",
            "s.send(req.SerializeToString())",
            "start = time.time()",
            "data = s.recv(2048)",
            "end = time.time() - start",
            "end_format = '{:.8f}'.format(end)",
            "filesize = sum(f.stat().st_size for f in Path(directory).glob('**/*') if f.is_file())",
            f"with open('{filename}', 'a', newline='') as results_file:",
            f"    half_str = 'criu_incremental_True,{notebook_name},{cell_num}'",
            """    results_file.write(half_str + ',checkpoint-time,' + end_format + '\\n')""",
            """    results_file.write(half_str + ',checkpoint-size,' + str(filesize) + '\\n')""",
        ]
    )


def get_dump_namespace_str(pickle_file_name: str, var_names: Optional[List[str]] = None) -> str:
    return "\n".join(
        [
            "import dill",
            "dill.dump({k: v for k, v in locals().items() if not k.startswith('_')",
            f"and k not in {Namespace.IPYTHON_VARS.union(KISHU_VARS)}",
            f"and (not {var_names} or k in {var_names})""},",
            f"open({repr(pickle_file_name)}, 'wb'))",
        ]
    )

def get_dill_dumpsession_str(notebook_name, filename, cell_num):
    return "\n".join(
        [
            "start = time.time()",
            f"dill.dump_session('/data/elastic-notebook/tmp/{notebook_name}_{cell_num}.pkl')",
            "end = time.time() - start",
            "end_format = '{:.8f}'.format(end)",
            "import os",
            f"filesize = os.stat('/data/elastic-notebook/tmp/{notebook_name}_{cell_num}.pkl').st_size",
            f"with open('{filename}', 'a', newline='') as results_file:",
            f"    half_str = 'dill,{notebook_name},{cell_num}'",
            """    results_file.write(half_str + ',checkpoint-time,' + end_format + '\\n')""",
            """    results_file.write(half_str + ',checkpoint-size,' + str(filesize) + '\\n')""",
        ]
    )


# def get_dill_dumpsession_str(notebook_name, filename, cell_num):
#     return "\n".join(
#         [
#             "start = time.time()",
#             f"dill.dump_session('/data/elastic-notebook/tmp/{notebook_name}_{cell_num}.pkl')",
#             "end = time.time() - start",
#             "end_format = '{:.8f}'.format(end)",
#             f"with open('{filename}', 'a', newline='') as results_file:",
#             f"    half_str = 'dill,{notebook_name},{cell_num}'",
#             """    results_file.write(half_str + ',checkpoint-time,' + end_format + '\\n')""",
#         ]
#     )


def get_dill_loadsession_str(notebook_name, filename, cell_num):
    return "\n".join(
        [
            "start2 = time.time()",
            f"dill.load_session('/data/elastic-notebook/tmp/{notebook_name}_{cell_num}.pkl')",
            "end = time.time() - start2",
            "end_format = '{:.8f}'.format(end)",
            f"with open('{filename}', 'a', newline='') as results_file:",
            f"    half_str = 'dill,{notebook_name},{cell_num}'",
            """    results_file.write(half_str + ',run_restore_time,' + end_format + '\\n')""",
        ]
    )


class NotebookRunner:
    """
    Executes specified cells in a Jupyter notebook and returns the output as a dictionary.

    Args:
        test_notebook (str): Path to the test notebook to be executed.
    """

    def __init__(self, test_notebook: str, notebook_name: str="temp"):
        """
        Initialize a NotebookRunner instance.

        Args:
            test_notebook (str): Path to the test notebook to be executed.
        """
        self.test_notebook = test_notebook
        self.notebook_name = notebook_name
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

    def execute_dill_test(self, cell_nums_to_restore: List[int]):
        # Open the notebook.
        with open(self.test_notebook) as nb_file:
            notebook = read(nb_file, as_version=4)

        filename = "/data/elastic-notebook/tmp/kishu_results.csv"

        # Strip all non-code (e.g., markdown) cells. We won't be needing them.
        notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]

        new_cells = []
        for i in range(len(notebook["cells"])):
            new_cells.append(notebook["cells"][i])
            new_cells.append(
                new_code_cell(source=get_dill_dumpsession_str(self.notebook_name, filename, i + 1)))

        # create a kishu initialization cell and add it to the start of the notebook.
        new_cells.insert(0, new_code_cell(source="import dill, time"))
        for i in range(len(notebook["cells"]), 0, -1):
        # for i in cell_nums_to_restore:
            new_cells.append(new_code_cell(source=get_dill_loadsession_str(self.notebook_name, filename, i)))

        notebook["cells"] = new_cells

        # Execute the notebook cells.
        exec_prep = ExecutePreprocessor(timeout=1200, kernel_name="python3")
        exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})

    def execute_criu_test(self, cell_num_to_restore: int, incremental_dump: bool):
        # Open the notebook.
        with open(self.test_notebook) as nb_file:
            notebook = read(nb_file, as_version=4)

        filename = "/data/elastic-notebook/tmp/kishu_results.csv"

        # Strip all non-code (e.g., markdown) cells. We won't be needing them.
        notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]
        print("pid:", os.getpid())

        new_cells = []
        for i in range(len(notebook["cells"])):
            new_cells.append(notebook["cells"][i])
            if incremental_dump:
                new_cells.append(
                    new_code_cell(source=get_criu_store_incremental_str(self.notebook_name, filename, i, os.getpid())))
            else:
                new_cells.append(
                    new_code_cell(source=get_criu_store_str(self.notebook_name, filename, i, os.getpid())))
        # create a kishu initialization cell and add it to the start of the notebook.
        new_cells.insert(0, new_code_cell(source="""
            import socket, os, sys, time
            from pathlib import Path
            import kishu_criu_pb2 as rpc
        """))
        #new_cells.append(new_code_cell(source=get_criu_store_str(self.notebook_name, filename, i)))

        notebook["cells"] = new_cells

        shell = InteractiveShell()

        for cell in notebook["cells"]:
            shell.run_cell(cell.source)

        # # Execute the notebook cells.
        # exec_prep = ExecutePreprocessor(timeout=1200, kernel_name="python3")
        # exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})

    def execute_incremental_load_test(self, cell_num_to_restore: int):
        # Open the notebook.
        with open(self.test_notebook) as nb_file:
            notebook = read(nb_file, as_version=4)

        # Strip all non-code (e.g., markdown) cells. We won't be needing them.
        notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]

        # create a kishu initialization cell and add it to the start of the notebook.
        notebook.cells.insert(0, new_code_cell(source=KISHU_INIT_STR))

        kishu_checkout_code = get_kishu_checkout_str(cell_num_to_restore)
        notebook.cells.append(new_code_cell(source=kishu_checkout_code))

        # Execute the notebook cells.
        exec_prep = ExecutePreprocessor(timeout=1200, kernel_name="python3")
        exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})

    def execute_full_checkout_test(self, cell_nums_to_restore: List[int]) -> Tuple[Dict, Dict]:
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
        # cell_num_to_restore += 1
        # assert cell_num_to_restore >= 2 and cell_num_to_restore <= len(notebook["cells"]) - 1

        # create a kishu initialization cell and add it to the start of the notebook.
        notebook.cells.insert(0, new_code_cell(source=KISHU_INIT_STR))

        # Insert dump session code at middle of notebook after the **cell_num_to_restore**th code cell.
        # dumpsession_code_middle = get_dump_namespace_str(self.pickle_file + ".middle")
        # notebook.cells.insert(cell_num_to_restore, new_code_cell(source=dumpsession_code_middle))

        # Insert kishu checkout code at end of notebook.
        for i in cell_nums_to_restore:
            kishu_checkout_code = get_kishu_checkout_str(i + 1)
            notebook.cells.append(new_code_cell(source=kishu_checkout_code))

        # Insert dump session code at end of notebook after kishu checkout.
        # dumpsession_code_end = get_dump_namespace_str(self.pickle_file + ".end")
        # notebook.cells.append(new_code_cell(source=dumpsession_code_end))

        # Execute the notebook cells.
        start = time.time()
        exec_prep = ExecutePreprocessor(timeout=6000, kernel_name="python3")
        exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})
        print("runtime:", time.time() - start)

        # get the output dumped namespace dictionaries.
        # data_middle = dill.load(open(self.pickle_file + '.middle', "rb"))
        # data_end = dill.load(open(self.pickle_file + '.end', "rb"))

        return None, None

    def execute_full_checkout_test2(self, cell_nums_to_restore: List[int]) -> Tuple[Dict, Dict]:
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
        # cell_num_to_restore += 1
        # assert cell_num_to_restore >= 2 and cell_num_to_restore <= len(notebook["cells"]) - 1

        # create a kishu initialization cell and add it to the start of the notebook.
        notebook.cells.insert(0, new_code_cell(source=KISHU_INIT_STR))

        # Insert dump session code at middle of notebook after the **cell_num_to_restore**th code cell.
        # dumpsession_code_middle = get_dump_namespace_str(self.pickle_file + ".middle")
        # notebook.cells.insert(cell_num_to_restore, new_code_cell(source=dumpsession_code_middle))

        # Insert kishu checkout code at end of notebook.
        # for i in range(len(notebook["cells"]) - 1, 0, -1):
        #     kishu_checkout_code = get_kishu_checkout_str(i)
        #     notebook.cells.append(new_code_cell(source=kishu_checkout_code))

        # Insert dump session code at end of notebook after kishu checkout.
        # dumpsession_code_end = get_dump_namespace_str(self.pickle_file + ".end")
        # notebook.cells.append(new_code_cell(source=dumpsession_code_end))

        # Execute the notebook cells.
        start = time.time()
        exec_prep = ExecutePreprocessor(timeout=6000, kernel_name="python3")
        exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})
        print("runtime:", time.time() - start)

        # get the output dumped namespace dictionaries.
        # data_middle = dill.load(open(self.pickle_file + '.middle', "rb"))
        # data_end = dill.load(open(self.pickle_file + '.end', "rb"))

        return None, None

    def execute_full_checkout_test3(self, cell_num_to_branch: int) -> Tuple[Dict, Dict]:
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

        original_cells = []
        for i in notebook["cells"]:
            original_cells.append(i)

        

        # The cell num to restore to should be valid. (the +1 is from the inserted kishu init cell below).
        # cell_num_to_restore += 1
        # assert cell_num_to_restore >= 2 and cell_num_to_restore <= len(notebook["cells"]) - 1

        # create a kishu initialization cell and add it to the start of the notebook.
        original_cells.insert(0, new_code_cell(source=KISHU_INIT_STR))

        # Insert dump session code at middle of notebook after the **cell_num_to_restore**th code cell.
        # dumpsession_code_middle = get_dump_namespace_str(self.pickle_file + ".middle")
        # notebook.cells.insert(cell_num_to_restore, new_code_cell(source=dumpsession_code_middle))

        # Insert kishu checkout code at end of notebook.
        kishu_checkout_code = get_kishu_checkout_str(cell_num_to_branch)
        original_cells.append(new_code_cell(source=kishu_checkout_code))

        branch_cells = []
        for i in range(cell_num_to_branch, len(notebook["cells"])):
            branch_cells.append(notebook["cells"][i])

        original_cells.extend(branch_cells)
        kishu_checkout_code = get_kishu_checkout_str(len(notebook["cells"]) - 4)
        original_cells.append(new_code_cell(source=kishu_checkout_code))
        # for i in range(len(notebook["cells"]) - 1, 0, -1):
        #     kishu_checkout_code = get_kishu_checkout_str(i)
        #     notebook.cells.append(new_code_cell(source=kishu_checkout_code))

        # Insert dump session code at end of notebook after kishu checkout.
        # dumpsession_code_end = get_dump_namespace_str(self.pickle_file + ".end")
        # notebook.cells.append(new_code_cell(source=dumpsession_code_end))

        # Execute the notebook cells.
        start = time.time()
        notebook.cells = original_cells
        exec_prep = ExecutePreprocessor(timeout=6000, kernel_name="python3")
        exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})
        print("runtime:", time.time() - start)

        # get the output dumped namespace dictionaries.
        # data_middle = dill.load(open(self.pickle_file + '.middle', "rb"))
        # data_end = dill.load(open(self.pickle_file + '.end', "rb"))

        return None, None
