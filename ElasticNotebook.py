from __future__ import print_function

import sys, traceback
import time

from IPython import get_ipython
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic)
from OptimizerType import OptimizerType

from elastic.core.common.profile_migration_speed import profile_migration_speed
from elastic.core.notebook.checkpoint import checkpoint
from elastic.core.notebook.inspect import inspect
from elastic.core.notebook.update_graph import update_graph
from elastic.core.notebook.find_input_output_vars import find_input_output_vars
from elastic.core.notebook.restore_notebook import restore_notebook

from elastic.core.graph.graph import DependencyGraph
from elastic.core.io.recover import resume

from elastic.algorithm.optimizer_exact import OptimizerExact
from elastic.algorithm.optimizer_greedy import OptimizerGreedy
from elastic.algorithm.baseline import RandomBaseline, RecomputeAllBaseline, MigrateAllBaseline


@magics_class
class ElasticNotebook(Magics):
    """
        Magics class for Elastic Notebook. Enable this in the notebook by running '%load_ext ElasticNotebook'.
        Enables efficient checkpointing of intermediate notebook state via balancing migration and recomputation
        costs.
    """
    def __init__(self, shell):
        super(ElasticNotebook, self).__init__(shell=shell)
        self.shell.configurables.append(self)

        # Initialize the dependency graph for capturing notebook state.
        self.dependency_graph = DependencyGraph()

        # Migration properties.
        self.migration_speed_bps = 100000
        self.selector = OptimizerExact(migration_speed_bps=self.migration_speed_bps)

        # Flag if migration speed has been manually set. In this case, skip profiling of migration speed at checkpoint
        # time.
        self.manual_migration_speed = False

        # Location to log runtimes to. For experiments only.
        self.write_log_location = None

        # Strings for determining log filename. For experiments only.
        self.optimizer_name = ""
        self.notebook_name = ""

    @cell_magic
    def RecordEvent(self, line, cell):
        """
            Cell magic for recording cell execution. Put %%RecordEvent at the 1st line of cells to record.
            Args:
                line: unused.
                cell: cell content.
        """

        # Run the cell.
        start_time = time.time()
        try:
            cell_output = get_ipython().run_cell(cell)
            cell_output.raise_error()
            traceback_list = []
        except:
            _, _, tb = sys.exc_info()
            traceback_list = traceback.extract_tb(tb).format()
        cell_runtime = time.time() - start_time

        # Find input and output variables of the cell.
        input_variables, output_variables = find_input_output_vars(
            cell, set(self.dependency_graph.variable_snapshots.keys()), self.shell, traceback_list)

        # Update the dependency graph.
        update_graph(cell, cell_runtime, start_time, input_variables, output_variables, self.dependency_graph)

    # Inspect the current state of the graph.
    @line_magic
    def Inspect(self, line=''):
        """
            %Inspect: Inspect the current notebook state. Displays a graph representation of the notebook with NetworkX.
            Args:
                line: unused.
        """

        inspect(self.dependency_graph)

    @line_magic
    def SetMigrationSpeed(self, migration_speed=''):
        """
            %SetMigrationSpeed x: Sets the migration speed to x. Can be used when the user has a reasonable estimation
            of the migration speed.
            Args:
                migration_speed: migration speed in bytes per second.
        """

        try:
            if float(migration_speed) > 0:
                self.migration_speed_bps = float(migration_speed)
                self.manual_migration_speed = True
            else:
                print("Migration speed is not positive.")
        except ValueError:
            print("Migration speed is not a number.")
        self.selector.migration_speed_bps = self.migration_speed_bps

    @line_magic
    def SetOptimizer(self, optimizer=''):
        """
            %SetOptimizer optimizer: Sets the optimization method to use for computing checkpointing configuration to
            'optimizer'.
            Args:
                optimizer: Optimizer to use.
        """
        self.optimizer_name = optimizer
        
        if optimizer == OptimizerType.EXACT.value:
            self.selector = OptimizerExact(self.migration_speed_bps)
        elif optimizer == OptimizerType.GREEDY.value:
            self.selector = OptimizerGreedy(self.migration_speed_bps)
        elif optimizer == OptimizerType.RANDOM.value:
            self.selector = RandomBaseline(self.migration_speed_bps)
        elif optimizer == OptimizerType.MIGRATE_ALL.value:
            self.selector = MigrateAllBaseline(self.migration_speed_bps)
        elif optimizer == OptimizerType.RECOMPUTE_ALL.value:
            self.selector = RecomputeAllBaseline(self.migration_speed_bps)

    @line_magic
    def SetWriteLogLocation(self, filename=''):
        """
            Sets the location to log runtimes to. For experiments only.
        """
        self.write_log_location = filename

    @line_magic
    def SetNotebookName(self, name=''):
        """
            Sets the notebook name for the log file. For experiments only.
        """
        self.notebook_name = name

    @line_magic
    def Checkpoint(self, filename=''):
        """
            %Checkpoint file.pickle: Checkpoints the notebook to the specified location.
            Args:
                filename: File to write checkpoint to. If empty, writes to a default location (see io/migrate.py).
        """
        # Profile the migration speed to filename.
        if not self.manual_migration_speed:
            self.migration_speed_bps = profile_migration_speed(filename)
            self.selector.migration_speed_bps = self.migration_speed_bps

        # Checkpoint the notebook.
        checkpoint(self.dependency_graph, self.shell, self.selector, filename, self.write_log_location,
                   self.notebook_name, self.optimizer_name)

    @line_magic
    def LoadCheckpoint(self, filename=''):
        """
            %LoadCheckpoint file.pickle: Load a checkpoint file and restore notebook state.
            Args:
                filename: File to read checkpoint from. If empty, reads from a default location (see io/migrate.py).
        """
        self.dependency_graph, variables, vss_to_migrate, vss_to_recompute, oes_to_recompute = \
            resume(filename, self.write_log_location, self.notebook_name, self.optimizer_name)

        # Recompute missing VSs and redeclare variables into the kernel.
        restore_notebook(self.dependency_graph, self.shell, variables, oes_to_recompute,
                         self.write_log_location, self.notebook_name, self.optimizer_name)


def load_ipython_extension(ipython):
    """
        Load the extension.
    """
    ipython.register_magics(ElasticNotebook)
