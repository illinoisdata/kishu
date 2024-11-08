from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import dill

from kishu.exceptions import MissingHistoryError
from kishu.jupyter.namespace import Namespace

# Alias for variable name
VariableName = FrozenSet[str]


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

    name: VariableName
    version: int


@dataclass
class VariableSnapshot:
    """
    A variable snapshot in the dependency graph corresponds to a version of a variable.
    I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have 3 corresponding
    variable snapshots.
        @param name: one or more variable names sharing references forming a connected component.
        @param version: time of creation or update to the corresponding variable name.
        @param deleted: whether this VS is created for the deletion of a variable, i.e., 'del x'.
        @param input_ces: Cell executions accessing this variable snapshot (i.e. require this variable snapshot to run).
        @param output_ce: The (unique) cell execution creating this variable snapshot.
    """

    name: VariableName
    version: int
    deleted: bool = False
    size: float = 0.0
    input_ces: List[CellExecution] = field(default_factory=lambda: [])
    output_ce: CellExecution = field(default_factory=lambda: CellExecution(0, "", 0.0, [], []))


@dataclass
class AHGUpdateInfo:
    """
    Dataclass containing all information for updating the AHG. Constructed and passed to the AHG after each cell
    execution.

    @param cell: Raw cell code.
    @param version: Version number of newly created VSes.
    @param cell_runtime_s: Cell runtime in seconds.
    @param accessed_variables: Set of accessed variables of the cell.
    @param current_variables: full list of variables in namespace post cell execution.
        Used to determine creations.
    @param linked_variable_pairs: pairs of linked variables.
    @param created_and_modified_variables: set of modified variables.
    @param deleted_variables: set of deleted variables.
    """

    cell: Optional[str] = None
    version: int = -1
    cell_runtime_s: float = 1.0
    accessed_variables: Set[str] = field(default_factory=set)
    current_variables: Set[str] = field(default_factory=set)
    linked_variable_pairs: List[Tuple[str, str]] = field(default_factory=lambda: [])
    modified_variables: Set[str] = field(default_factory=set)
    deleted_variables: Set[str] = field(default_factory=set)


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

        # All variable snapshots which have existed at some point in the session.
        # Keys are the name-version tuples of variable snapshots (VersionedName) for fast lookup.
        # The values are the actual VariableSnapshots.
        self._variable_snapshots: Dict[VersionedName, VariableSnapshot] = {}

        # Variable snapshots that are currently active, i.e., their values are currently in the namespace.
        # The keys are the names of the variable snapshots for fast lookup.
        # The values are a subset of the values of self._variable_snapshots.
        self._active_variable_snapshots: Dict[VariableName, VariableSnapshot] = {}

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
            keyset_list = list(user_ns.keyset())
            linked_variable_pairs = [(keyset_list[i], keyset_list[i + 1]) for i in range(len(keyset_list) - 1)]

            ahg.update_graph(
                AHGUpdateInfo(
                    cell=existing_cell_executions[0],
                    version=time.monotonic_ns(),
                    cell_runtime_s=1.0,
                    current_variables=user_ns.keyset(),
                    linked_variable_pairs=linked_variable_pairs,
                )
            )

            # Subsequent cell executions has all existing variables as input and output variables.
            for i in range(1, len(existing_cell_executions)):
                ahg.update_graph(
                    AHGUpdateInfo(
                        cell=existing_cell_executions[i],
                        version=time.monotonic_ns(),
                        cell_runtime_s=1.0,
                        accessed_variables=user_ns.keyset(),
                        current_variables=user_ns.keyset(),
                        linked_variable_pairs=linked_variable_pairs,
                        modified_variables=user_ns.keyset(),
                    )
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

    def update_graph(self, update_info: AHGUpdateInfo) -> None:
        """
        Updates the graph according to the newly executed cell and its input and output variables.
        """
        cell = "" if not update_info.cell else update_info.cell

        # Retrieve accessed variable snapshots. A VS is accessed if any of the names in its connected component are accessed.
        accessed_vss = [
            vs for vs in self._active_variable_snapshots.values() if vs.name.intersection(update_info.accessed_variables)
        ]

        # Compute the set of current connected components of variables in the namespace.
        connected_components_set = AHG.union_find(update_info.current_variables, update_info.linked_variable_pairs)

        # If a new component does not exactly match an existing component, it is treated as a created VS.
        output_vss_create = [
            VariableSnapshot(k, update_info.version, False)
            for k in connected_components_set
            if k not in self._active_variable_snapshots.keys()
        ]

        # An active VS (from the previous cell exec) is still active only if it exactly matches a connected component and
        # wasn't modified.
        unmodified_still_active_vss = {
            k: v
            for k, v in self._active_variable_snapshots.items()
            if k in connected_components_set and not k.intersection(update_info.modified_variables)
        }

        # An (active) VS is modified if (1) its variable membership has not changed
        # during the cell execution (i.e., in connected_components_set) and (2) at
        # least 1 of its member variables were modified.
        output_vss_modify = [
            VariableSnapshot(frozenset(v.name), update_info.version, False)
            for k, v in self._active_variable_snapshots.items()
            if k in connected_components_set and v.name.intersection(update_info.modified_variables)
        ]

        # Deleted VSes are always singletons of the deleted names.
        output_vss_delete = [VariableSnapshot(frozenset(k), update_info.version, False) for k in update_info.deleted_variables]

        # Add a CE to the graph.
        output_vss = output_vss_create + output_vss_modify + output_vss_delete
        self.add_cell_execution(cell, update_info.cell_runtime_s, accessed_vss, output_vss)

        # Add output VSes to the graph.
        self._variable_snapshots = {
            **self._variable_snapshots,
            **{VersionedName(vs.name, vs.version): vs for vs in output_vss},
        }

        # Update set of active VSes (those still active from previous cell exec + created VSes + modified VSes).
        self._active_variable_snapshots = {
            **unmodified_still_active_vss,
            **{vs.name: vs for vs in output_vss_create + output_vss_modify},
        }

    def get_cell_executions(self) -> List[CellExecution]:
        return self._cell_executions

    def get_variable_snapshots(self) -> List[VariableSnapshot]:
        return list(self._variable_snapshots.values())

    def get_active_variable_snapshots(self) -> List[VariableSnapshot]:
        return list(self._active_variable_snapshots.values())

    def get_active_variable_snapshots_dict(self) -> Dict[VariableName, VariableSnapshot]:
        return self._active_variable_snapshots

    def get_variable_names(self) -> Set[str]:
        # Return all variable KVs in components as a flattened set.
        return set(chain.from_iterable(self._active_variable_snapshots.keys()))

    def serialize(self) -> str:
        """
        Returns the decoded serialized bytestring (str type) of the AHG.
        Required as the AHG is not JSON serializable by default.
        """
        return dill.dumps(self).decode("latin1")

    @staticmethod
    def deserialize(ahg_string: str) -> AHG:
        """
        Returns the AHG object from serialized AHG in string format.
        """
        return dill.loads(ahg_string.encode("latin1"))

    def clone(self) -> AHG:
        """
        Deep copies all fields (e.g., VSes, cell executions) into a new AHG. For testing.
        """
        return AHG.deserialize(self.serialize())

    def get_vs_by_versioned_name(self, versioned_name: VersionedName) -> VariableSnapshot:
        return self._variable_snapshots[versioned_name]

    def serialize_active_vses(self) -> str:
        return dill.dumps([VersionedName(vs.name, vs.version) for vs in self.get_active_variable_snapshots()]).decode("latin1")

    @staticmethod
    def deserialize_active_vses(active_vs_string: str) -> List[VersionedName]:
        return dill.loads(active_vs_string.encode("latin1"))

    def clone_active_vses(self) -> List[VersionedName]:
        return AHG.deserialize_active_vses(self.serialize_active_vses())

    def replace_active_vses(self, versioned_names: List[VersionedName]) -> None:
        """
        Replaces the active VSes of the current AHG.
        """
        self._active_variable_snapshots.clear()
        for versioned_name in versioned_names:
            self._active_variable_snapshots[versioned_name.name] = self._variable_snapshots[versioned_name]

    @staticmethod
    def union_find(variables: Set[str], linked_variables: List[Tuple[str, str]]) -> Set[VariableName]:
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
