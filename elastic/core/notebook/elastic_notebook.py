from __future__ import print_function

import re
import sys
from collections import defaultdict
import time

from IPython import get_ipython
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic)

from elastic.core.notebook.checkpoint import checkpoint
from elastic.core.notebook.inspect import inspect
from elastic.core.notebook.update_graph import update_graph
from elastic.core.graph.graph import DependencyGraph
from elastic.core.io.recover import resume
from elastic.core.notebook.restore_notebook import restore_notebook


# The class MUST call this class decorator at creation time
@magics_class
class ElasticNotebook(Magics):

    def __init__(self, shell):
        super(ElasticNotebook, self).__init__(shell=shell)
        self.shell.configurables.append(self)

        # Dependency graph for capturing notebook state.
        self.dependency_graph = DependencyGraph()

    # Records a cell execution.
    @cell_magic
    def RecordEvent(self, line, cell):
        start_time = time.time()
        # Actually run the cell code.
        get_ipython().run_cell(cell)
        cell_runtime = time.time() - start_time

        # Update the dependency graph.
        update_graph(cell, cell_runtime, start_time, self.dependency_graph)

    # Inspect the current state of the graph.
    @line_magic
    def Inspect(self, line=''):
        inspect(self.dependency_graph)

    # Checkpoints the notebook to the specified location.
    @line_magic
    def Checkpoint(self, filename=''):
        checkpoint(self.dependency_graph, self.shell, filename)

    # Loads the checkpoint from the specified location.
    @line_magic
    def LoadCheckpoint(self, filename=''):
        self.dependency_graph, variables, vss_to_migrate, vss_to_recompute, oes_to_recompute = resume(filename)

        # Recompute missing VSs and redeclare variables into the kernel.
        restore_notebook(self.dependency_graph, variables, oes_to_recompute, self.shell)

# Load the extension.
def load_ipython_extension(ipython):
    ipython.register_magics(ElasticNotebook)
