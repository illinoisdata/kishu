from __future__ import annotations

import functools
import time
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from kishu.exceptions import MissingHistoryError
from kishu.jupyter.namespace import Namespace
from kishu.planning.profiler import profile_variable_size
from kishu.storage.commit_graph import CommitId
from kishu.storage.diskahg import KishuDiskAHG

# TODO(Billy): Many of these primitive classes may be moved to disk_ahg.py to avoid circular import.


CellExecutionId = int


class VariableName(FrozenSet[str]):

    def encode_name(self) -> str:
        return repr(sorted(self))

    @staticmethod
    def decode_name(encoded_name: str) -> VariableName:
        return VariableName(
            [name.strip().replace("'", "") for name in encoded_name.replace("[", "").replace("]", "").split(",")]
        )


@dataclass(frozen=True)
class CellExecution:
    """
    A cell execution (object) corresponds to a cell execution (action, i.e. press play) in the notebook session.

    @param cell_num: The nth cell execution of the current session.
    @param cell: Raw cell code.
    @param cell_runtime_s: Cell runtime in seconds.
    @param src_vss: List containing input VSs of the cell execution.
    @param dst_vss: List containing output VSs of the cell execution.
    """

    cell_num: CellExecutionId
    cell: str
    cell_runtime_s: float


@dataclass(frozen=True)
class VersionedName:
    """
    Simplified name-version representation of a Variable Snapshot. Hashable and immutable.
    """

    name: VariableName
    version: int


@dataclass(frozen=True)
class VariableSnapshot:
    """
    A variable snapshot in the dependency graph corresponds to a version of a variable.
    I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have 3 corresponding
    variable snapshots.
        @param name: one or more variable names sharing references forming a connected component.
        @param version: time of creation or update to the corresponding variable name.
        @param deleted: whether this VS is created for the deletion of a variable, i.e., 'del x'.
        @param output_ce: The (unique) cell execution creating this variable snapshot.
    """

    name: VariableName
    version: int
    deleted: bool
    size: float

    @staticmethod
    def select_names_from_update(update_info: AHGUpdateInfo, name: VariableName) -> VariableSnapshot:
        size = profile_variable_size([update_info.user_ns[var] for var in name])
        return VariableSnapshot(
            name=name,
            version=update_info.version,
            deleted=False,
            size=size,
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


@dataclass
class AHGUpdateResult:
    """
    New items from an AHG update to persist to database.
    """

    accessed_vss: List[VariableSnapshot]
    output_vss: List[VariableSnapshot]
    newest_ce: CellExecution

    # TODO(Billy): Write this to self._disk_ahg
    active_variable_snapshots: Dict[VariableName, VariableSnapshot]


class AHG:
    """
    The Application History Graph (AHG) tracks the history of a notebook instance.
    Variable Snapshots (VSs) and Cell Executions (CEs) are the nodes of the AHG.
    Edges represent dependencies between VSs and CEs.
    """

    def __init__(self, disk_ahg: KishuDiskAHG) -> None:
        """
        Create a new AHG. Called when Kishu is initialized for a notebook.
        """
        self._disk_ahg = disk_ahg

    @staticmethod
    def from_db(
        disk_ahg: KishuDiskAHG,
        user_ns: Namespace,
    ) -> AHG:
        ahg = AHG(disk_ahg)
        ahg._augment_existing(user_ns)
        return ahg

    def _augment_existing(self, user_ns: Namespace) -> Optional[AHGUpdateResult]:
        """
        Augments the current AHG with a dummy cell execution representing existing untracked cell executions.
        """
        # Throw error if there are existing variables but the cell executions are missing.
        existing_cell_executions = user_ns.ipython_in()
        if existing_cell_executions is not None and len(existing_cell_executions) == 0 and len(user_ns.keyset()) > 0:
            raise MissingHistoryError()

        # First cell execution has no input variables and outputs all existing variables.
        if existing_cell_executions:
            # Assume that all variables in the namespace form 1 giant connected component.
            keyset_list = list(user_ns.keyset())
            linked_variable_pairs = [(keyset_list[i], keyset_list[i + 1]) for i in range(len(keyset_list) - 1)]

            # This dummy cell execution consists of all untracked code, accesses nothing, and deletes all VSes
            # which are no longer in the namespace.
            self.update_graph(
                AHGUpdateInfo(
                    cell="\n".join(existing_cell_executions),
                    version=time.monotonic_ns(),
                    current_variables=user_ns.keyset(),
                    linked_variable_pairs=linked_variable_pairs,
                    deleted_variables=self.get_active_variable_names().difference(user_ns.keyset()),
                )
            )
        return None

    def update_graph(self, update_info: AHGUpdateInfo):
        """
        Updates the graph according to the newly executed cell and its input and output variables.
        """
        current_active_variable_snapshots = self.get_active_variable_snapshots_dict(update_info.commit_id)

        # Retrieve accessed variable snapshots. A VS is accessed if any of the names in its connected component are accessed.
        accessed_vss = [
            vs for vs in current_active_variable_snapshots.values() if vs.name.intersection(update_info.accessed_variables)
        ]

        # Compute the set of current connected components of variables in the namespace.
        connected_components_set = AHG.union_find(update_info.current_variables, update_info.linked_variable_pairs)

        # If a new component does not exactly match an existing component, it is treated as a created VS.
        output_vss_create = [
            VariableSnapshot.select_names_from_update(update_info, k)
            for k in connected_components_set
            if k not in current_active_variable_snapshots.keys()
        ]

        # An active VS (from the previous cell exec) is still active only if it exactly matches a connected component and
        # wasn't modified.
        unmodified_still_active_vss = {
            k: v
            for k, v in current_active_variable_snapshots.items()
            if k in connected_components_set and not k.intersection(update_info.modified_variables)
        }

        # An (active) VS is modified if (1) its variable membership has not changed
        # during the cell execution (i.e., in connected_components_set) and (2) at
        # least 1 of its member variables were modified.
        output_vss_modify = [
            VariableSnapshot.select_names_from_update(update_info, VariableName(v.name))
            for k, v in current_active_variable_snapshots.items()
            if k in connected_components_set and v.name.intersection(update_info.modified_variables)
        ]

        # Deleted VSes are always singletons of the deleted names.
        output_vss_delete = [
            VariableSnapshot.select_names_from_update(update_info, VariableName({k})) for k in update_info.deleted_variables
        ]

        # TODO(Bill): Add comment?
        output_vss = output_vss_create + output_vss_modify + output_vss_delete

        # Update set of active VSes (those still active from previous cell exec + created VSes + modified VSes).
        active_variable_snapshots = {
            **unmodified_still_active_vss,
            **{vs.name: vs for vs in output_vss_create + output_vss_modify},
        }
        newest_ce = CellExecution(
            cell_num=self.get_next_cell_num(update_info.parent_commit_id),
            cell="" if not update_info.cell else update_info.cell,
            cell_runtime_s=update_info.cell_runtime_s,
        )

        # Persist AHG updates to disk.
        self._disk_ahg.store_update_results(
            AHGUpdateResult(
                accessed_vss=accessed_vss,
                output_vss=output_vss,
                newest_ce=newest_ce,
                active_variable_snapshots=active_variable_snapshots,
            )
        )

    """Cell Executions."""

    @functools.lru_cache(maxsize=None)
    def get_cell_executions_dict(self, commit_id: CommitId) -> Dict[int, CellExecution]:
        past_commit_ids = ...  # TODO(Billy): Get this from commit graph.
        return self._disk_ahg.get_batch_cell_executions(past_commit_ids)

    def get_cell_executions(self, commit_id: CommitId) -> List[CellExecution]:
        return self.get_cell_executions_dict(commit_id).values()

    @functools.lru_cache(maxsize=None)
    def get_next_cell_num(self, commit_id: CommitId) -> int: ...  # TODO(Billy): Get from _disk_ahg

    """Variable snapshots."""

    @functools.lru_cache(maxsize=None)
    def get_variable_snapshot(self, versioned_name: VersionedName) -> List[VariableSnapshot]:
        return self._disk_ahg.get_variable_snapshot(versioned_name)

    """Active variable snapshots."""

    @functools.lru_cache(maxsize=None)
    def get_active_variable_snapshots_dict(self, commit_id: CommitId) -> Dict[VariableName, VariableSnapshot]:
        return self._disk_ahg.get_active_variable_snapshots_dict(commit_id)

    def get_active_variable_snapshots(self, commit_id: CommitId) -> List[VariableSnapshot]:
        return list(self.get_active_variable_snapshots_dict(commit_id).values())

    def get_active_variable_names(self, commit_id: CommitId) -> Set[str]:
        # Return all variable KVs in components as a flattened set.
        return set(chain.from_iterable(self.get_active_variable_snapshots_dict(commit_id).keys()))

    @functools.lru_cache(maxsize=None)
    def get_vs_by_versioned_name(self, versioned_name: VersionedName) -> VariableSnapshot:
        return self._disk_ahg.get_vs_by_versioned_name(versioned_name)

    @functools.lru_cache(maxsize=None)
    def get_source_variable_snapshots(self, cell_num: CellExecutionId) -> List[VariableSnapshot]:
        # TODO(Billy): Get this from _disk_ahg.
        # TODO(Billy): In place of `source_vss` use this function.
        return ...

    @functools.lru_cache(maxsize=None)
    def get_destination_variable_snapshots(self, cell_num: CellExecutionId) -> List[VariableSnapshot]:
        # TODO(Billy): Get this from _disk_ahg.
        # TODO(Billy): In place of `dst_vss` use this function.
        return ...

    @functools.lru_cache(maxsize=None)
    def get_output_cell_execution(self, versioned_name: VersionedName) -> CellExecution:
        # TODO(Billy): Get this from _disk_ahg.
        # TODO(Billy): In place of `output_ce` use this function.
        return ...

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
        return set(VariableName(v) for v in connected_components_dict.values())
