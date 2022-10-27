import path
import sys
# directory reach
directory = path.Path(__file__).abspath()
# setting path
sys.path.append(directory.parent.parent)

"""
TODO: update this experiment script. See 'numpy.ipynb' for an example annotated notebook and 'numpy_restore.ipynb'
for an example notebook recovery.

Annotated notebook summary:
DONE    1. Create a cell with this line:
        %load_ext elastic.core.notebook.elastic_notebook
        This may require setting up the syspath.
DONE    2. Set the log location and notebook name, i.e. %SetWriteLogLocation file.py, %SetNotebookName numpy
DONE    3. Add %%RecordEvent before the first line of each cell.
DONE    4. Set the optimizer, i.e. %SetOptimizer exact. See 'ElasticNotebook.py' for a list of optimizers.
DONE    5. Either set or profile the migration speed, i.e. %ProfileMigrationSpeed file.pickle / 
        %SetMigrationSpeed 100000.  
        -------->>>>>> Write speed for data directory = 200MB/s i.e 200000000 bps
DONE    6. Migrate the notebook: %Checkpoint file.py

Recovery notebook summary:
DONE    1. Create a cell with this line:
        %load_ext elastic.core.notebook.elastic_notebook
        This may require setting up the syspath.
DONE    2. Set the log location, notebook name, and optimizer, i.e. %SetWriteLogLocation file.py, %SetNotebookName numpy,
        %SetOptimizer exact.
    3. Recover the notebook: %LoadCheckpoint file.py
"""

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

class ExperimentCode:

    LOAD_EXT = """
import sys, os
sys.path.insert(0, os.path.abspath("../.."))
%load_ext ElasticNotebook
"""

    RECORD_EVENT = """
%%RecordEvent
"""

    def set_optimizer(optimizerName):
        return """
%SetOptimizer """+optimizerName+"""
"""

    def set_write_location(writeLogLocation):
        return """
%SetWriteLogLocation """+writeLogLocation+"""
"""

    def set_notebook_name(notebookName):
        return """
%SetNotebookName """+notebookName+"""
"""

    def set_migration_speed(migrationSpeed):
        return """
%SetMigrationSpeed """+migrationSpeed+"""
"""

    def migrate_notebook(fileName):
        return """
%Checkpoint """+fileName+"""
"""

    def load_checkpoint(fileName):
        return """
%LoadCheckpoint """+fileName+"""
"""


# Run the given notebook with the given optimizer
def run_experiment(notebook="numpy.ipynb", optimizer="exact"):
    # Experiment Code has code cells predefined

    e = ExperimentCode

    
    directory = "notebooks/"
    log_location = "results/"
    migration_speed = "200000000" #bps
    migration_file_name = "checkpoint/"+notebook+".pickle"
    # read notebook
    with open(directory + notebook) as f:
        nb = nbformat.read(f, as_version=4)

    # Append "RecordEvent" magic function to all code cells
    for cell in nb["cells"]:
        if(cell["cell_type"] == "code"):
            cell["source"] = e.RECORD_EVENT + cell["source"]

    # Inserting code to load ElasticNotebook magic class to the start of the notebook
    nb["cells"].insert(0,nbformat.v4.new_code_cell(e.LOAD_EXT))

    # Adding code to checkpoint notebook
    nb["cells"] += [nbformat.v4.new_code_cell(e.set_optimizer(optimizer)),
                    nbformat.v4.new_code_cell(e.set_write_location(log_location)),
                    nbformat.v4.new_code_cell(e.set_notebook_name(notebook)),
                    nbformat.v4.new_code_cell(e.set_migration_speed(migration_speed)),
                    nbformat.v4.new_code_cell(e.migrate_notebook(migration_file_name))]

    # Print to check if cells have been modified appropriately
    i = 1
    for cell in nb["cells"]:
        print("cell source -",i," = \n",cell["source"])
        print("\n")
        i+=1


    # execute the updated notebook
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb)

    # Reconstruction
    nb_recover = nbformat.v4.new_notebook()
    nb_recover["cells"] += [nbformat.v4.new_code_cell(e.LOAD_EXT),
                            nbformat.v4.new_code_cell(e.set_optimizer(optimizer)),
                            nbformat.v4.new_code_cell(e.set_write_location(log_location)),
                            nbformat.v4.new_code_cell(e.set_notebook_name(notebook)),
                            nbformat.v4.new_code_cell(e.load_checkpoint(migration_file_name))]

    # Print to check if cells have been modified appropriately
    # i = 1
    # for cell in nb_recover["cells"]:
    #     print("cell source -",i," = \n",cell["source"])
    #     print("\n")
    #     i+=1

    ep.preprocess(nb_recover)