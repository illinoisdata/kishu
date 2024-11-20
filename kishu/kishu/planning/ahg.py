from __future__ import annotations

import functools
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from typing import Dict, FrozenSet, List, Set, Tuple

from kishu.jupyter.namespace import Namespace
from kishu.storage.commit_graph import CommitId
from kishu.storage.disk_ahg import (
    AHGUpdateResult,
    CellExecution,
    CellExecutionNumber,
    KishuDiskAHG,
    VariableName,
    VariableSnapshot,
)


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

    parent_commit_id: CommitId
    commit_id: CommitId
    user_ns: Namespace
    cell: str = ""
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

    This class is the cached in-memory of the KishuDiskAHG which handles optimization logic.
    """

    def __init__(self, disk_ahg: KishuDiskAHG) -> None:
        """
        Create a new AHG. Called when Kishu is initialized for a notebook.
        """
        self._disk_ahg = disk_ahg

        # Existing cells in the session prior to Kishu being attached.
        self._existing_cells: str = ""

    @staticmethod
    def from_db(
        disk_ahg: KishuDiskAHG,
        existing_cell_executions: List[str],
    ) -> AHG:
        ahg = AHG(disk_ahg)
        ahg._augment_existing(existing_cell_executions)
        return ahg

    def _augment_existing(self, existing_cell_executions: List[str]) -> None:
        """
        Augments the current AHG with a dummy cell execution representing existing untracked cell executions.
        """
        # Create a dummy cell execution containing concatenated code of all existing cell executions.
        if existing_cell_executions:
            self._existing_cells = "\n".join(existing_cell_executions)

    def update_graph(self, update_info: AHGUpdateInfo) -> None:
        """
        Updates the graph according to the newly executed cell and its input and output variables.
        """
        current_active_variables = self.get_active_variable_snapshots(update_info.parent_commit_id)

        # Retrieve accessed variable snapshots. A VS is accessed if any of the names in its connected component are accessed.
        accessed_vss = [vs for vs in current_active_variables if vs.name.intersection(update_info.accessed_variables)]

        # Compute the set of current connected components of variables in the namespace.
        connected_components_set = AHG.union_find(update_info.current_variables, update_info.linked_variable_pairs)

        # If a new component does not exactly match an existing component, it is treated as a created VS.
        output_vss_create = [
            VariableSnapshot.select_names_from_update(update_info.user_ns, update_info.version, name)
            for name in connected_components_set
            if name not in [vs.name for vs in current_active_variables]
        ]

        # An active VS (from the previous cell exec) is still active only if it exactly matches a connected component and
        # wasn't modified.
        unmodified_still_active_vss = [
            vs
            for vs in current_active_variables
            if vs.name in connected_components_set and not vs.name.intersection(update_info.modified_variables)
        ]

        # An (active) VS is modified if (1) its variable membership has not changed
        # during the cell execution (i.e., in connected_components_set) and (2) at
        # least 1 of its member variables were modified.
        output_vss_modify = [
            VariableSnapshot.select_names_from_update(update_info.user_ns, update_info.version, name)
            for name in [vs.name for vs in current_active_variables]
            if name in connected_components_set and name.intersection(update_info.modified_variables)
        ]

        # Deleted VSes are always singletons of the deleted names.
        output_vss_delete = [
            VariableSnapshot(frozenset({k}), update_info.version, True) for k in update_info.deleted_variables
        ]

        # Output VSes consists of VSes created/modified/deleted in this cell execution.
        output_vss = output_vss_create + output_vss_modify + output_vss_delete

        cell = update_info.cell

        # If there are untracked cell executions, prepend them to the current cell.
        if self._existing_cells:
            cell = f"{self._existing_cells}\n{cell}"
            self._existing_cells = ""

        newest_ce = CellExecution(update_info.version, cell, update_info.cell_runtime_s)

        # Update set of active VSes (those still active from previous cell exec + created VSes + modified VSes).
        new_active_variables = unmodified_still_active_vss + output_vss_create + output_vss_modify

        self._disk_ahg.store_update_results(
            AHGUpdateResult(update_info.commit_id, accessed_vss, output_vss, newest_ce, new_active_variables)
        )

    def get_all_cell_executions(self) -> Set[CellExecution]:
        return set(self._disk_ahg.get_all_cell_executions())

    def get_all_variable_snapshots(self) -> Set[VariableSnapshot]:
        return set(self._disk_ahg.get_all_variable_snapshots())

    @functools.lru_cache(maxsize=None)
    def get_active_variable_snapshots(self, commit_id: CommitId) -> Set[VariableSnapshot]:
        return set(self._disk_ahg.get_active_vses(commit_id))

    @functools.lru_cache(maxsize=None)
    def get_active_variable_names(self, commit_id: CommitId) -> Set[str]:
        # Return all variable KVs in components as a flattened set.
        return set(chain.from_iterable([vs.name for vs in self.get_active_variable_snapshots(commit_id)]))

    @functools.lru_cache(maxsize=None)
    def get_vs_by_versioned_names(self, versioned_names: FrozenSet[str]) -> Set[VariableSnapshot]:
        """
        The conversion is for caching.
        """
        return set(self._disk_ahg.get_vs_by_versioned_names(list(versioned_names)))

    @functools.lru_cache(maxsize=None)
    def get_ce_by_cell_num(self, cell_num: CellExecutionNumber) -> CellExecution:
        return self._disk_ahg.get_ce_by_cell_num(cell_num)

    @functools.lru_cache(maxsize=None)
    def get_vs_input_ce(self, vs: VariableSnapshot) -> CellExecution:
        return self._disk_ahg.get_vs_input_ce(vs)

    @functools.lru_cache(maxsize=None)
    def get_ce_input_vses(self, ce: CellExecution) -> Set[VariableSnapshot]:
        return set(self._disk_ahg.get_ce_input_vses(ce))

    def get_ce_output_vses(self, ce: CellExecution) -> Set[VariableSnapshot]:
        """
        This is explicitly not cached as the VSes a CE contributes to is not immutable.
        """
        return set(self._disk_ahg.get_ce_output_vses(ce))

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
