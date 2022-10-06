import path
import sys
# directory reach
directory = path.Path(__file__).abspath()
# setting path
sys.path.append(directory.parent.parent)

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

class ExperimentCode:

        CREATE_GRAPH = """
import time
# get the start time for stage 1
start_stage_1 = time.time()
from core.notebook.create_graph import create_graph
graph = create_graph()
graph_creation = time.time()"""

        def trim_graph(optimizerName) :
                trim = """
# Use the optimizer to find nodes to migrate
from algorithm.optimizer_greedy import OptimizerGreedy
from algorithm.optimizer_exact import OptimizerExact
from algorithm.baseline import MigrateAllBaseline
from algorithm.baseline import RecomputeAllBaseline
from algorithm.baseline import RandomBaseline

trim_start = time.time()
"""
                if(optimizerName == "Exact"):
                        trim += """opt = OptimizerExact(migration_speed_bps=100000)"""
                elif(optimizerName == "Greedy"):
                        trim += """opt = OptimizerGreedy(migration_speed_bps=100000)"""
                elif(optimizerName == "Baseline_Migrate"):
                        trim += """opt = MigrateAllBaseline(migration_speed_bps=100000)"""
                elif(optimizerName == "Baseline_Recompute"):
                        trim += """opt = RecomputeAllBaseline(migration_speed_bps=100000)"""
                elif(optimizerName == "Baseline_Random"):
                        trim += """opt = RandomBaseline(migration_speed_bps=100000)"""
                
                trim += """
optimizerName = '"""+optimizerName+"""'
graph.trim_graph(opt)
trim_stop = time.time()

# ******************************** How to run baseline? ***************************************
# trim_base_start = time.time()
# opt = OptimizerGreedy(migration_speed_bps=100000)
# graph.trim_graph(opt)
# trim_base_stop = time.time()
"""
                return trim

        MIGRATE = """
# Migrate the dependency graph.
migration_start = time.time()
from core.io.filesystem_adapter import FilesystemAdapter
from core.io.migrate import migrate

migrate(graph, FilesystemAdapter())

migration_stop = time.time()
"""
        def time_stage_1(notebookName):
                                return """from datetime import datetime
with open""" +\
"""('../results/output_""" + notebookName + """_' + """ + """ optimizerName """ + """ +'.txt', 'w') as f:
\tf.write("-------- Current time --------" + str(datetime.now()) + "\\n")
\tf.write('Graph creation stage took - '+ repr(graph_creation-start_stage_1) + " seconds" + '\\n')
\tf.write(optimizerName + ' trimming stage took - '+ repr(trim_stop-trim_start) + " seconds" + '\\n')
\tf.write('Migration stage took - '+ repr(migration_stop-migration_start) + " seconds" + '\\n')
\tf.write('Stage 1 - Migration took - '+ repr(migration_stop-start_stage_1) + " seconds" + '\\n')
"""

        RECOVER = """from core.io.filesystem_adapter import FilesystemAdapter
from core.io.recover import resume

start_stage_2 = time.time()
graph = resume(FilesystemAdapter())

recover_end = time.time()
"""

        RECOMPUTE = """# Recompute trimmed nodes.
graph.recompute_graph(globals())

recompute_end = time.time()
"""

        RESTORE = """# Reconstruct the notebook by declaring variables and functions into the kernel.
graph.reconstruct_notebook()

restore_end = time.time()
"""

        def time_stage_2(notebookName):
                return """with open""" +\
"""('../results/output_""" + notebookName + """_' + """ + """optimizerName""" + """+'.txt', 'a') as f:
\tf.write('\\nRecovery stage took - '+ repr(recover_end-start_stage_2) + " seconds" + '\\n')
\tf.write('Recompute stage took - '+ repr(recompute_end-recover_end) + " seconds" + '\\n')
\tf.write('Restore stage took - '+ repr(restore_end-recompute_end) + " seconds" + '\\n')
\tf.write('Stage 2 - Restoration took - '+ repr(restore_end-start_stage_2) + " seconds" + '\\n')
"""

# Run the given notebook with the given optimizer
def run_experiment(notebook = "numpy.ipynb", optimizer = "Exact"):

        # Experiment Code has code cells for all stages
        # Stage 1 - Graph creation, trimming graph using optimizer and migration
        # Stage 2 - Recover, recompute and restore
        e = ExperimentCode
        
        # read notebook
        directory = "notebooks/"
        with open(directory+notebook) as f:
                nb = nbformat.read(f,as_version=4)

        # add code cells
        nb["cells"] += [nbformat.v4.new_code_cell(e.CREATE_GRAPH),
                        nbformat.v4.new_code_cell(e.trim_graph(optimizer)),
                        nbformat.v4.new_code_cell(e.MIGRATE),
                        nbformat.v4.new_code_cell(e.RECOVER),
                        nbformat.v4.new_code_cell(e.RECOMPUTE),
                        nbformat.v4.new_code_cell(e.RESTORE),
                        nbformat.v4.new_code_cell(e.time_stage_1(notebook)),
                        nbformat.v4.new_code_cell(e.time_stage_2(notebook))]

        # execute the updated notebook
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': 'notebooks/'}})
