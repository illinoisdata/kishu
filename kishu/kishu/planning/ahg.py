from __future__ import annotations

import dill
import time

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

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


@dataclass(frozen=True)
class VersionedName:
    """
        Simplified name-version representation of a Variable Snapshot. Hashable and immutable.
    """
    name: FrozenSet[str]
    version: int


@dataclass(frozen=True)
class VersionedNameContext:
    """
        Info related to a versioned name stored in the databse.
    """
    size: int
    commit_id: str


@dataclass
class VariableSnapshot:
    """
        A variable snapshot in the dependency graph corresponds to a version of a variable.
        I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have 3 corresponding
        variable snapshots.
        Multiple variables sharing references are treated as 1 'large' variable, e.g., ('x', 'y', 'z').

        @param name: one or more variable names sharing references forming a connected component.
        @param version: time of creation or update to the corresponding variable name.
        @param deleted: whether this VS is created for the deletion of a variable, i.e., 'del x'.
        @param input_ces: Cell executions accessing this variable snapshot (i.e. require this variable snapshot to run).
        @param output_ce: The (unique) cell execution creating this variable snapshot.
    """
    name: FrozenSet[str]
    version: int
    deleted: bool = False
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

        # All variable snapshots in the session.
        self._variable_snapshots: List[VariableSnapshot] = []

        # Variable snapshots that are currently active, i.e., their values are currently in the namespace.
        # The keys are the names of the variable snapshots for fast lookup.
        # The values are a subset of self._variable_snapshots.
        self._active_variable_snapshots: Dict[FrozenSet[str], VariableSnapshot] = {}

    @staticmethod
    def from_existing(user_ns: Namespace) -> AHG:
        ahg = AHG()

        # Throw error if there are existing variables but the cell executions are missing.
        existing_cell_executions = user_ns.ipython_in()
        if not existing_cell_executions and user_ns.keyset():
            raise MissingHistoryError()

        # First cell execution has no input variables and outputs all existing variables.
        if existing_cell_executions:
            # Assume that all variables in the namespace form 1 giant connected component.
            linked_variable_pairs = []
            if len(user_ns.keyset()) >= 2:
                keyset_list = list(user_ns.keyset())
                linked_variable_pairs = [(keyset_list[i], keyset_list[i + 1]) for i in range(len(keyset_list) - 1)]

            ahg.update_graph(
                existing_cell_executions[0],
                time.monotonic_ns(),
                1.0,
                set(),
                user_ns.keyset(),
                linked_variable_pairs,
                set(),
                set()
            )

            # Subsequent cell executions has all existing variables as input and output variables.
            for i in range(1, len(existing_cell_executions)):
                ahg.update_graph(
                    existing_cell_executions[i],
                    time.monotonic_ns(),
                    1.0,
                    set(),
                    user_ns.keyset(),
                    linked_variable_pairs,
                    user_ns.keyset(),
                    set()
                )

        return ahg

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

    def update_graph(self,
                     cell: Optional[str],
                     version: int,
                     cell_runtime_s: float,
                     input_variables: Set[str],
                     current_variables: Set[str],
                     linked_variable_pairs: List[Tuple[str, str]],
                     modified_variables: Set[str],
                     deleted_variables: Set[str]) -> None:
        """
            Updates the graph according to the newly executed cell and its input and output variables.

            @param cell: Raw cell code.
            @param version: Version number of newly created VSes.
            @param cell_runtime_s: Cell runtime in seconds.
            @param input_variables: Set of input variables of the cell.
            @param created_and_modified_variables: set of created and modified variables.
            @param deleted_variables: set of deleted variables.
        """
        cell = "" if not cell else cell

        # Retrieve input variable snapshots. A VS is an input if any of the names in its connected component are accessed.
        input_vss = [vs for vs in self._active_variable_snapshots.values() if vs.name.intersection(input_variables)]

        # If a variable is unserializable (i.e., inf size), assume that it is modified on access.
        # unserializable_vars = [vs for vs in self._active_variable_snapshots.values() if vs.size == float('inf')]
        # for vs in unserializable_vars:
        #     if vs.name.intersection(input_variables):
        #         modified_variables.update(vs.name)

        # Compute the set of current connected components of variables in the namespace.
        connected_components_set = AHG.union_find(current_variables, linked_variable_pairs)

        # If a new component does not exactly match an existing component, it is treated as a created variable.
        output_vss_create = [VariableSnapshot(k, version, False) for k in connected_components_set if
                             k not in self._active_variable_snapshots.keys()]

        # Filter: if an active variable's connected component no longer exists, it is no longer active.
        self._active_variable_snapshots = {
            k: v for k, v in self._active_variable_snapshots.items() if k in connected_components_set}

        # A variable is modified if any name in its connected component is modified.
        output_vss_modify = [VariableSnapshot(frozenset(vs.name), version, False)
                             for vs in self._active_variable_snapshots.values() if
                             vs.name.intersection(modified_variables)]

        # Filter: if an active variable's connected component has been modified, it is no longer active.
        self._active_variable_snapshots = {k: v for k, v in self._active_variable_snapshots.items()
                                           if not k.intersection(modified_variables)}

        output_vss_delete = [VariableSnapshot(frozenset(k), version, False) for k in deleted_variables]

        # Add the newly created CE to the graph.
        self.add_cell_execution(cell, cell_runtime_s, input_vss, output_vss_create + output_vss_modify + output_vss_delete)

        # Add created and modified VSes to the active variables list.
        self._active_variable_snapshots.update({vs.name: vs for vs in output_vss_create})
        self._active_variable_snapshots.update({vs.name: vs for vs in output_vss_modify})
        self._variable_snapshots += output_vss_create + output_vss_modify + output_vss_delete

    def get_cell_executions(self) -> List[CellExecution]:
        return self._cell_executions

    def get_variable_snapshots(self) -> List[VariableSnapshot]:
        return self._variable_snapshots

    def get_active_variable_snapshots(self) -> List[VariableSnapshot]:
        return list(self._active_variable_snapshots.values())

    def get_active_variable_snapshots_dict(self) -> Dict[FrozenSet[str], VariableSnapshot]:
        return self._active_variable_snapshots

    def get_variable_names(self) -> Set[str]:
        # Return all variable KVs in components as a flattened set.
        return set(chain.from_iterable(self._active_variable_snapshots.keys()))

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

    @staticmethod
    def union_find(variables: Set[str], linked_variables: List[Tuple[str, str]]) -> Set[FrozenSet[str]]:
        roots: Dict[str, str] = {}

        def find_root(var: str) -> str:
            if roots.get(var, var) == var:
                return var
            roots[var] = find_root(roots[var])
            return roots[var]

        # Union find iterations.
        for var1, var2 in linked_variables:
            root_var1 = find_root(var1)
            root_var2 = find_root(var2)
            roots[root_var2] = root_var1

        # Flatten all connected components.
        roots = {var: find_root(var) for var in variables}

        # Return the list of connected components.
        connected_components_dict = defaultdict(set)
        for var, var_root in roots.items():
            connected_components_dict[var_root].add(var)
        return set(frozenset(v) for v in connected_components_dict.values())
