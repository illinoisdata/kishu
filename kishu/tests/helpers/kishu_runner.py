import os
import time
from IPython.core.interactiveshell import InteractiveShell

from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell
import argparse

NOTEBOOK_DIR = "tests/notebooks/"

KISHU_INIT_STR: str = "from kishu import init_kishu; init_kishu();"


def get_kishu_checkout_str(cell_num: int, session_num: int = 1) -> str:
    return f"_kishu.checkout('{session_num}:{cell_num}')"


def execute_kishu_test(notebook_name, cell_nums_to_restore):
    # Open the notebook.
    with open(notebook_name) as nb_file:
        notebook = read(nb_file, as_version=4)

    filename = "/data/elastic-notebook/tmp/kishu_results.csv"

    # Strip all non-code (e.g., markdown) cells. We won't be needing them.
    notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]

    # The notebook should have at least 2 cells to run this test.
    assert len(notebook["cells"]) >= 2

    # The cell num to restore to should be valid. (the +1 is from the inserted kishu init cell below).

    # create a kishu initialization cell and add it to the start of the notebook.
    notebook.cells.insert(0, new_code_cell(source=KISHU_INIT_STR))

    # Insert dump session code at middle of notebook after the **cell_num_to_restore**th code cell.
    # dumpsession_code_middle = get_dump_namespace_str(self.pickle_file + ".middle")
    # notebook.cells.insert(cell_num_to_restore, new_code_cell(source=dumpsession_code_middle))

    # Insert kishu checkout code at end of notebook.
    for i in cell_nums_to_restore:
        kishu_checkout_code = get_kishu_checkout_str(i + 1)
        notebook.cells.append(new_code_cell(source=kishu_checkout_code))

    shell = InteractiveShell()

    for cell in notebook["cells"]:
        shell.run_cell(cell.source)

    # # Execute the notebook cells.
    # exec_prep = ExecutePreprocessor(timeout=1200, kernel_name="python3")
    # exec_prep.preprocess(notebook, {"metadata": {"path": self.path_to_notebook}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--notebook_name", help="Number of nodes in generated graph")
    parser.add_argument("-C", "--cell_num_to_restore", help="Memory container size")
    parser.add_argument("-I", "--incremental_dump", help="Number of iterations to run")
    args = parser.parse_args()

    default_n_threads = 8
    os.environ['OPENBLAS_NUM_THREADS'] = f"{default_n_threads}"
    os.environ['MKL_NUM_THREADS'] = f"{default_n_threads}"
    os.environ['OMP_NUM_THREADS'] = f"{default_n_threads}"

    start = time.time()
    execute_criu_test(args.notebook_name, args.cell_num_to_restore, args.incremental_dump == "True")
    print("total time:", time.time() - start)