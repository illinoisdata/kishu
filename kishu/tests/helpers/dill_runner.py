import os
import time
from IPython.core.interactiveshell import InteractiveShell

from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell
import argparse

NOTEBOOK_DIR = "tests/notebooks/"

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
            "start = time.time()",
            f"dill.load_session('/data/elastic-notebook/tmp/{notebook_name}_{cell_num}.pkl')",
            "end = time.time() - start",
            "end_format = '{:.8f}'.format(end)",
            f"with open('{filename}', 'a', newline='') as results_file:",
            f"    half_str = 'dill,{notebook_name},{cell_num}'",
            """    results_file.write(half_str + ',run_restore_time,' + end_format + '\\n')""",
        ]
    )

def execute_dill_test(notebook_name, cell_nums_to_restore):
    # Open the notebook.
    with open(NOTEBOOK_DIR + notebook_name) as nb_file:
        notebook = read(nb_file, as_version=4)

    filename = "/data/elastic-notebook/tmp/kishu_results.csv"

    # Strip all non-code (e.g., markdown) cells. We won't be needing them.
    notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]

    new_cells = []
    for i in range(len(notebook["cells"])):
        new_cells.append(notebook["cells"][i])
        new_cells.append(
            new_code_cell(source=get_dill_dumpsession_str(notebook_name, filename, i + 1)))

    # create a kishu initialization cell and add it to the start of the notebook.
    new_cells.insert(0, new_code_cell(source="import dill, time"))
    for i in cell_nums_to_restore:
        new_cells.append(new_code_cell(source=get_dill_loadsession_str(notebook_name, filename, i)))

    notebook["cells"] = new_cells

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