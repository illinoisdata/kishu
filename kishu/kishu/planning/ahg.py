from __future__ import annotations

import dill

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from kishu.exceptions import MissingHistoryError
from kishu.jupyter.namespace import Namespace


@dataclass
class CellExecution:
    """
        A cell execution (object) corresponds to a cell execution (action, i.e. press play) in the notebook session.

        @param cell_num: The nth cell execution of the current session.
        @param cell: Raw cell code.
        @param cell_runtime_s: Cell runtime in seconds.
        @param src_vss: List containing input VSs of the cell execution.
        @param dst_vss: List containing output VSs of the cell execution.
    """
    cell_num: int
    cell: str
    cell_runtime_s: float
    src_vss: List[VariableSnapshot]
    dst_vss: List[VariableSnapshot]


@dataclass
class VariableSnapshot:
    """
        A variable snapshot in the dependency graph corresponds to a version of a variable.
        I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have 3 corresponding
        variable snapshots.

        @param name: variable name.
        @param version: nth update to the corresponding variable name.
        @param deleted: whether this VS is created for the deletion of a variable, i.e., 'del x'.
        @param input_ces: Cell executions accessing this variable snapshot (i.e. require this variable snapshot to run).
        @param output_ce: The (unique) cell execution creating this variable snapshot.
    """
    name: str
    version: int
    deleted: bool
    size: float = 0.0
    input_ces: List[CellExecution] = field(default_factory=lambda: [])
    output_ce: CellExecution = field(default_factory=lambda: CellExecution(0, "", 0.0, [], []))


class AHG:
    """
        The Application History Graph (AHG) tracks the history of a notebook instance.
        Variable Snapshots (VSs) and Cell Executions (CEs) are the nodes of the AHG.
        Edges represent dependencies between VSs and CEs.
    """
    def __init__(self) -> None:
        """
            Create a new AHG. Called when Kishu is initialized for a notebook.
        """
        # Cell executions in chronological order.
        self._cell_executions: List[CellExecution] = []

        # Dict of variable snapshots.
        # Keys are variable names, while values are lists of the actual VSs.
        # i.e. {"x": [(x, 1), (x, 2)], "y": [(y, 1), (y, 2), (y, 3)]}
        self._variable_snapshots: Dict[str, List[VariableSnapshot]] = defaultdict(list)

    @staticmethod
    def from_existing(user_ns: Namespace) -> AHG:
        ahg = AHG()

        # Throw error if there are existing variables but the cell executions are missing.
        existing_cell_executions = user_ns.ipython_in()
        if not existing_cell_executions and user_ns.keyset():
            raise MissingHistoryError()

        # First cell execution has no input variables and outputs all existing variables.
        if existing_cell_executions:
            ahg.update_graph(existing_cell_executions[0], 1.0, set(), user_ns.keyset(), set())

            # Subsequent cell executions has all existing variables as input and output variables.
            for i in range(1, len(existing_cell_executions)):
                ahg.update_graph(existing_cell_executions[i], 1.0, user_ns.keyset(), user_ns.keyset(), set())

        return ahg

    def create_variable_snapshot(self, variable_name: str, deleted: bool) -> VariableSnapshot:
        """
            Creates a new variable snapshot for a given variable.

            @param variable_name: name of variable.
            @param deleted: Whether this VS is created for the deletion of a variable, i.e. 'del x'.
        """
        # Assign a version number to the VS.
        version = len(self._variable_snapshots[variable_name]) if variable_name in self._variable_snapshots else 0

        # Create a new VS instance and store it in the graph.
        vs = VariableSnapshot(variable_name, version, deleted)
        self._variable_snapshots[variable_name].append(vs)
        return vs

    def add_cell_execution(
        self,
        cell: str,
        cell_runtime_s: float,
        src_vss: List[VariableSnapshot],
        dst_vss: List[VariableSnapshot],
    ) -> None:
        """
            Create a cell execution from captured metrics.

            @param cell: Raw cell code.
            @param cell_runtime_s: Cell runtime in seconnds.
            @param src_vss: List containing input VSs of the cell execution.
            @param dst_vss: List containing output VSs of the cell execution.
        """
        # Create a cell execution.
        ce = CellExecution(len(self._cell_executions), cell, cell_runtime_s, src_vss, dst_vss)

        # Add the newly created cell execution to the graph.
        self._cell_executions.append(ce)

        # Set the newly created cell execution as dependent on its input variable snapshots.
        for src_vs in src_vss:
            src_vs.input_ces.append(ce)

        # Set the newly created cell execution as the parent of its output variable snapshots.
        for dst_vs in dst_vss:
            dst_vs.output_ce = ce

    def update_graph(self, cell: Optional[str], cell_runtime_s: float, input_variables: Set[str],
                     created_and_modified_variables: Set[str], deleted_variables: Set[str]) -> None:
        """
            Updates the graph according to the newly executed cell and its input and output variables.

            @param cell: Raw cell code.
            @param cell_runtime_s: Cell runtime in seconds.
            @param input_variables: Set of input variables of the cell.
            @param created_and_modified_variables: set of created and modified variables.
            @param deleted_variables: set of deleted variables.
        """
        cell = "" if not cell else cell

        # Retrieve input variable snapshots
        input_vss = [self._variable_snapshots[variable][-1] for variable in input_variables]

        # Create output variable snapshots
        output_vss_create = [self.create_variable_snapshot(k, False) for k in created_and_modified_variables]
        output_vss_delete = [self.create_variable_snapshot(k, True) for k in deleted_variables]

        # Add the newly created CE to the graph.
        self.add_cell_execution(cell, cell_runtime_s, input_vss, output_vss_create + output_vss_delete)

    def get_cell_executions(self) -> List[CellExecution]:
        return self._cell_executions

    def get_variable_snapshots(self) -> Dict[str, List[VariableSnapshot]]:
        return self._variable_snapshots

    def serialize(self) -> str:
        """
            Returns the decoded serialized bytestring (str type) of the AHG.
            Required as the AHG is not JSON serializable by default.
        """
        return dill.dumps(self).decode('latin1')

    @staticmethod
    def deserialize(ahg_string: str) -> AHG:
        """
            Returns the AHG object from serialized AHG in string format.
        """
        return dill.loads(ahg_string.encode('latin1'))
