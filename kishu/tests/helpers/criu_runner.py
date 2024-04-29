import os
import time
from IPython.core.interactiveshell import InteractiveShell
from ipykernel.zmqshell import ZMQInteractiveShell
from ipyflow.shell.interactiveshell import IPyflowInteractiveShell

from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell
import argparse
import pickle

NOTEBOOK_DIR = "tests/notebooks/"
# NOTEBOOK_DIR = ""

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
            "resp = rpc.criu_resp()",
            "resp.ParseFromString(s.recv(2048))",
            "end = time.time() - start",
            "end_format = '{:.8f}'.format(end)",
            "filesize = 0",
            "for f in Path(directory).glob('**/*'):",
            "    if f.is_file():",
            "        filesize += f.stat().st_size",
            #"filesize = sum(f.stat().st_size for f in Path(directory).glob('**/*') if f.is_file())",
            f"with open('{filename}', 'a', newline='') as results_file:",
            f"    half_str = 'criu_incremental_False,{notebook_name},{cell_num}'",
            """    results_file.write(half_str + ',checkpoint-time,' + end_format + '\\n')""",
            """    results_file.write(half_str + ',checkpoint-size,' + str(filesize) + '\\n')""",
            """    results_file.write(half_str + ',success,' + str(resp.success) + '\\n')""",
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
            "filesize = 0",
            "for f in Path(directory).glob('**/*'):",
            "    if f.is_file():",
            "        filesize += f.stat().st_size",
            #"filesize = sum(f.stat().st_size for f in Path(directory).glob('**/*') if f.is_file())",
            f"with open('{filename}', 'a', newline='') as results_file:",
            f"    half_str = 'criu_incremental_True,{notebook_name},{cell_num}'",
            """    results_file.write(half_str + ',checkpoint-time,' + end_format + '\\n')""",
            """    results_file.write(half_str + ',checkpoint-size,' + str(filesize) + '\\n')""",
        ]
    )

def execute_criu_test(notebook_name, cell_num_to_restore: int, incremental_dump: bool):
    # Open the notebook.
    with open(NOTEBOOK_DIR + notebook_name) as nb_file:
        notebook = read(nb_file, as_version=4)

    filename = "/data/elastic-notebook/tmp/kishu_results.csv"

    # Strip all non-code (e.g., markdown) cells. We won't be needing them.
    notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]
    print("pid:", os.getpid())

    new_cells = []
    for i in range(len(notebook["cells"])):
        new_cells.append(notebook["cells"][i])
        if i == len(notebook["cells"]) - 1:
            if incremental_dump:
                new_cells.append(
                    new_code_cell(source=get_criu_store_incremental_str(notebook_name, filename, i, os.getpid())))
            else:
                new_cells.append(
                    new_code_cell(source=get_criu_store_str(notebook_name, filename, i, os.getpid())))

    # Initialize CRIU rpc.
    new_cells.insert(0, new_code_cell(source="""
        import socket, os, sys, time
        from pathlib import Path
        import kishu_criu_pb2 as rpc
    """))

    notebook["cells"] = new_cells

    shell = InteractiveShell()

    for cell in notebook["cells"]:
        shell.run_cell(cell.source)


def execute_ipyflow_test(notebook_name, cell_num_to_restore: int, incremental_dump: bool):
    # Open the notebook.
    with open(NOTEBOOK_DIR + notebook_name) as nb_file:
        notebook = read(nb_file, as_version=4)

    filename = "/data/elastic-notebook/tmp/kishu_results.csv"

    # Strip all non-code (e.g., markdown) cells. We won't be needing them.
    notebook["cells"] = [x for x in notebook["cells"] if x["cell_type"] == "code"]

    new_raw_cells = []
    new_ipyflow_cells = []
    for i in range(len(notebook["cells"])):
        new_raw_cells.append(notebook["cells"][i])
        new_ipyflow_cells.append(notebook["cells"][i])

    # create a kishu initialization cell and add it to the start of the notebook.
    new_ipyflow_cells.insert(0, new_code_cell(source="""
        %load_ext ipyflow
    """))
    #new_cells.append(new_code_cell(source=get_criu_store_str(self.notebook_name, filename, i)))

    # shell = InteractiveShell()
    # for cell in new_raw_cells:
    #     shell.run_cell(cell.source)

    # raw_times = []
    # shell = InteractiveShell()
    # for cell in new_raw_cells:
    #     start = time.time()
    #     shell.run_cell(cell.source)
    #     raw_times.append(time.time() - start)

    ipyflow_times = []
    shell = IPyflowInteractiveShell().instance()
    for cell in new_ipyflow_cells[1:]:
        start = time.time()
        shell.run_cell(cell.source)
        ipyflow_times.append(time.time() - start)

    # diff = [ipyflow_times[i] - raw_times[i] for i in range(len(raw_times))]
    # print(ipyflow_times)
    # print(raw_times)
    # print(diff)
    # print(sum(diff))

    # with open(f'/data/elastic-notebook/tmp/{notebook_name}_ipyflow_diff.pkl', 'wb') as f:  # open a text file
    #     pickle.dump(diff, f) # serialize the list
    with open(f'/data/elastic-notebook/tmp/{notebook_name}_ipyflow_diff1.pkl', 'wb') as f:  # open a text file
        pickle.dump(ipyflow_times, f) # serialize the list

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