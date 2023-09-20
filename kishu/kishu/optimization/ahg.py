import logging
from collections import defaultdict
from typing import List

class VariableSnapshot:
    """
        A variable snapshot in the dependency graph corresponds to a version of a variable.
        I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have 3 corresponding
        variable snapshots.
    """
    def __init__(self, name: str, version: int, deleted: bool):
        """
            Create a variable snapshot from variable properties.
            Args:
                name (str): Variable name.
                version (int): The nth update to the corresponding variable.
                deleted (bool): Whether this VS is created for the deletion of a variable, i.e. 'del x'.
        """
        self.name = name
        self.version = version

        # Whether this VS corresponds to a deleted variable.
        # i.e. if this VS was created for 'del x' we set this to true so this variable is explicitly not considered
        # for migration.
        self.deleted = deleted

        # Cell executions accessing this variable snapshot (i.e. require this variable snapshot to run).
        self.input_ces = []

        # The unique cell execution creating this variable snapshot.
        self.output_ce = None


class CellExecution:
    """
        A cell execution (object) corresponds to a cell execution (action, i.e. press play) in the notebook session.
    """
    def __init__(self, cell_num: int, cell: str, cell_runtime: float, start_time: float, src_vss: List, dst_vss: List):
        """
            Create an operation event from cell execution metrics.
            Args:
                cell_num (int): The nth cell execution of the current session.
                cell (str): Raw cell cell.
                cell_runtime (float): Cell runtime.
                start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                    queued.
                src_vss (List[VariableSnapshot]): Nodeset containing input VSs of the cell execution.
                dst_vss (List[VariableSnapshot]): Nodeset containing output VSs of the cell execution.
        """
        self.cell_num = cell_num
        self.cell = cell
        self.cell_runtime = cell_runtime
        self.start_time = start_time

        self.src_vss = src_vss
        self.dst_vss = dst_vss


class AHG:
    """
        The Application History Graph (AHG) tracks the history of a notebook instance.
        Variable Snapshots (VSs) and Cell Executions (CEs) are the nodes of the AHG.
        Edges represent dependencies between VSs and CEs.
    """
    def __init__(self):
        """
            Create a new AHG. Called when Kishu is initialized for a notebook.
        """
        # Cell executions.
        self.cell_executions = []

        # Dict of variable snapshots.
        # Keys are variable names, while values are lists of the actual VSs.
        # i.e. {"x": [(x, 1), (x, 2)], "y": [(y, 1), (y, 2), (y, 3)]}
        self.variable_snapshots = defaultdict(list)

    def create_variable_snapshot(self, variable_name: str, deleted: bool) -> VariableSnapshot:
        """
            Creates a new variable snapshot for a given variable.
            Args:
                variable_name (str): variable_name
                deleted (bool): Whether this VS is created for the deletion of a variable, i.e. 'del x'.
        """

        # Assign a version number to the VS.
        if variable_name in self.variable_snapshots:
            version = len(self.variable_snapshots[variable_name])
        else:
            version = 0

        # Create a new VS instance and store it in the graph.
        vs = VariableSnapshot(variable_name, version, deleted)
        self.variable_snapshots[variable_name].append(vs)
        return vs

    def add_cell_execution(self, cell, cell_runtime: float, start_time: float, src_vss: List, dst_vss: List):
        """
            Create a cell execution from captured metrics.
            Args:
                cell (str): Raw cell cell.
                cell_runtime (float): Cell runtime.
                start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                    queued.
                src_vss (List): List containing input VSs of the cell execution.
                dst_vss (List): List containing output VSs of the cell execution.
        """

        # Create a cell execution.
        ce = CellExecution(len(self.cell_executions), cell, cell_runtime, start_time, src_vss, dst_vss)

        # Add the newly created cell execution to the graph.
        self.cell_executions.append(ce)

        # Set the newly created cell execution as dependent on its input variable snapshots.
        for src_vs in src_vss:
            src_vs.input_ces.append(ce)

        # Set the newly created cell execution as the parent of its output variable snapshots.
        for dst_vs in dst_vss:
            dst_vs.output_ce = ce


    def update_graph(self, cell: str, cell_runtime: float, start_time: float, input_variables: set,
                 created_and_modified_variables: set, deleted_variables: set):
        """
            Updates the graph according to the newly executed cell and its input and output variables.
            Args:
                cell (str): Raw cell cell.
                cell_runtime (float): Cell runtime.
                start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                    queued.
                input_variables (set): Set of input variables of the cell.
                created_and_modified_variables (set): set of created and modified variables.
                deleted_variables (set): set of deleted variables
        """

        # Retrieve input variable snapshots
        input_vss = set(self.variable_snapshots[variable][-1] for variable in input_variables)

        # Create output variable snapshots
        output_vss_create = set(self.create_variable_snapshot(k, False) for k in created_and_modified_variables)
        output_vss_delete = set(self.create_variable_snapshot(k, True) for k in deleted_variables)

        # Add the newly created OE to the graph.
        self.add_cell_execution(cell, cell_runtime, start_time, input_vss, output_vss_create.union(output_vss_delete))
        print("cell executions:", len(self.cell_executions))
