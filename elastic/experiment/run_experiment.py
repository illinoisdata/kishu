from elastic.algorithm.selector import OptimizerType
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


LOAD_EXT = """
import sys, os
sys.path.insert(0, os.path.abspath("../.."))
%load_ext ElasticNotebook
"""

RECORD_EVENT = """
%%RecordEvent
"""

DIRECTORY = "notebooks/"

LOG_LOCATION = "/data/elastic-notebook/results"

MIGRATION_FILE_DIR = "/data/elastic-notebook/checkpoints/"


def set_optimizer(optimizer_name):
    return """
%SetOptimizer """+optimizer_name+"""
"""


def set_write_location(write_log_location):
    return """
%SetWriteLogLocation """+write_log_location+"""
"""


def set_notebook_name(notebook_name):
    return """
%SetNotebookName """+notebook_name+"""
"""


def set_migration_speed(migration_speed):
    return """
%SetMigrationSpeed """+migration_speed+"""
"""


def migrate_notebook(filename):
    return """
%Checkpoint """+filename+"""
"""


def load_checkpoint(filename):
    return """
%LoadCheckpoint """+filename+"""
"""


# Run the given notebook with the given optimizer
def run_notebook(notebook="numpy.ipynb"):
    """
        Run the specified notebook and create a checkpoint using each optimizer.
    """
    # Experiment Code has code cells predefined
    migration_file_name = MIGRATION_FILE_DIR + notebook + ".pickle"
    migration_speed = "150000000"  # bps

    # read notebook
    with open(DIRECTORY + notebook) as f:
        nb = nbformat.read(f, as_version=4)

    # Append "RecordEvent" magic function to all code cells
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = RECORD_EVENT + cell["source"]

    # Inserting code to load ElasticNotebook magic class to the start of the notebook
    nb["cells"].insert(0, nbformat.v4.new_code_cell(LOAD_EXT))

    # Add checkpointing code for each optimizer
    for optimizer_enum in OptimizerType:
        # Adding code to checkpoint notebook
        nb["cells"] += [nbformat.v4.new_code_cell(set_optimizer(optimizer_enum.value)),
                        nbformat.v4.new_code_cell(set_write_location(LOG_LOCATION)),
                        nbformat.v4.new_code_cell(set_notebook_name(notebook)),
                        nbformat.v4.new_code_cell(set_migration_speed(migration_speed)),
                        nbformat.v4.new_code_cell(migrate_notebook(migration_file_name + "_" + optimizer_enum.value))]

    # execute the updated notebook
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb)


def restore_notebook(notebook="numpy.ipynb", optimizer='exact'):
    """
        Restore a notebook from the specified checkpoint.
    """
    migration_file_name = MIGRATION_FILE_DIR + notebook + ".pickle"

    # Reconstruction
    nb_recover = nbformat.v4.new_notebook()
    nb_recover["cells"] += [nbformat.v4.new_code_cell(LOAD_EXT),
                            nbformat.v4.new_code_cell(set_optimizer(optimizer)),
                            nbformat.v4.new_code_cell(set_write_location(LOG_LOCATION)),
                            nbformat.v4.new_code_cell(set_notebook_name(notebook)),
                            nbformat.v4.new_code_cell(load_checkpoint(migration_file_name + "_" + optimizer))]

    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb_recover)
