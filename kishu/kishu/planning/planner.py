from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import chain, combinations
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import AHG, AHGUpdateInfo, VariableName, VersionedName
from kishu.planning.idgraph import GraphNode, get_object_state, value_equals
from kishu.planning.optimizer import IncrementalLoadOptimizer, Optimizer
from kishu.planning.plan import CheckpointPlan, IncrementalCheckpointPlan, RestorePlan
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.commit import CommitEntry, KishuCommit
from kishu.storage.commit_graph import CommitId, KishuCommitGraph
from kishu.storage.diskahg import KishuDiskAHG


@dataclass
class ChangedVariables:
    created_vars: Set[str]

    # Modified vars by value equality , i.e., a == b.
    modified_vars_value: Set[str]

    # modified vars by memory structure (i.e., reference swaps). Is a superset of modified_vars_value.
    modified_vars_structure: Set[str]

    deleted_vars: Set[str]

    def added(self):
        return self.created_vars | self.modified_vars_value

    def deleted(self):
        return self.deleted_vars


@dataclass
class UsefulVses:
    """
    Currently active VSes and stored VSes (in the database) that can help restoration. Constructed during
    computation of incremental restore plan.
    """

    useful_active_vses: Set[VersionedName]
    useful_stored_vses: Set[VersionedName]


class CheckpointRestorePlanner:
    """
    The CheckpointRestorePlanner class holds items (e.g., AHG) relevant for creating
    the checkpoint and restoration plans during notebook runtime.
    """

    def __init__(
        self,
        user_ns: Namespace = Namespace(),
        ahg: Optional[AHG] = None,
        kishu_graph: Optional[KishuCommitGraph] = None,
        kishu_commit: Optional[KishuCommit] = None,
        kishu_disk_ahg: Optional[KishuDiskAHG] = None,
        incremental_cr: bool = False,
    ) -> None:
        """
        @param user_ns  User namespace containing variables in the kernel.
        """
        self._ahg = ahg if ahg else AHG()
        self._user_ns = user_ns
        self._id_graph_map: Dict[str, GraphNode] = {}
        self._pre_run_cell_vars: Set[str] = set()

        # C/R plan configs.
        self._incremental_cr = incremental_cr

        # Storage-related items.
        self._kishu_graph = kishu_graph
        self._kishu_commit = kishu_commit
        self._kishu_disk_ahg = kishu_disk_ahg

        # Used by instrumentation to compute whether data has changed.
        self._modified_vars_structure: Set[str] = set()

    @staticmethod
    def from_existing(
        user_ns: Namespace,
        kishu_graph: KishuCommitGraph,
        kishu_commit: KishuCommit,
        kishu_disk_ahg: KishuDiskAHG,
        incremental_cr: bool,
    ) -> CheckpointRestorePlanner:
        cr_planner = CheckpointRestorePlanner(user_ns, None, kishu_graph, kishu_commit, kishu_disk_ahg, incremental_cr)

        # Initialize AHG with records stored in the disk AHG DB.
        cr_planner._ahg = AHG.from_db(kishu_disk_ahg, user_ns)

        return cr_planner

    def pre_run_cell_update(self) -> None:
        """
        Preprocessing steps performed prior to cell execution.
        """
        # Record variables in the user name prior to running cell.
        self._pre_run_cell_vars = self._user_ns.keyset()

        # Populate missing ID graph entries.
        for var in self._ahg.get_active_variable_names():
            if var not in self._id_graph_map and var in self._user_ns:
                self._id_graph_map[var] = get_object_state(self._user_ns[var], {})

    def post_run_cell_update(self, code_block: Optional[str], runtime_s: Optional[float]) -> ChangedVariables:
        """
        Post-processing steps performed after cell execution.
        @param code_block: code of executed cell.
        @param runtime_s: runtime of cell execution.
        """
        # Use current timestamp as version for new VSes to be created during the update.
        version = time.monotonic_ns()

        # Find accessed variables from monkey-patched namespace.
        accessed_vars = self._user_ns.accessed_vars().intersection(self._pre_run_cell_vars)
        self._user_ns.reset_accessed_vars()

        # Find created and deleted variables
        created_vars = self._user_ns.keyset().difference(self._pre_run_cell_vars)
        deleted_vars = self._pre_run_cell_vars.difference(self._user_ns.keyset())

        # Find modified variables.
        modified_vars_structure = set()
        modified_vars_value = set()
        for k in filter(self._user_ns.__contains__, self._id_graph_map.keys()):
            new_idgraph = get_object_state(self._user_ns[k], {})

            # Identify objects which have changed by value. For displaying in front end.
            if not value_equals(self._id_graph_map[k], new_idgraph):
                modified_vars_value.add(k)

            if not self._id_graph_map[k] == new_idgraph:
                # Non-overwrite modification requires also accessing the variable.
                if self._id_graph_map[k].is_root_id_and_type_equals(new_idgraph):
                    accessed_vars.add(k)
                self._id_graph_map[k] = new_idgraph
                modified_vars_structure.add(k)

        # Update ID graphs for newly created variables.
        for var in created_vars:
            self._id_graph_map[var] = get_object_state(self._user_ns[var], {})

        # Find pairs of linked variables.
        linked_var_pairs = []
        for x, y in combinations(self._user_ns.keyset(), 2):
            if self._id_graph_map[x].is_overlap(self._id_graph_map[y]):
                linked_var_pairs.append((x, y))

        # Update AHG.
        runtime_s = 0.0 if runtime_s is None else runtime_s
        self._ahg.update_graph(
            AHGUpdateInfo(
                code_block,
                version,
                runtime_s,
                accessed_vars,
                self._user_ns.keyset(),
                linked_var_pairs,
                modified_vars_structure,
                deleted_vars,
            )
        )

        return ChangedVariables(created_vars, modified_vars_value, modified_vars_structure, deleted_vars)

    def generate_checkpoint_restore_plans(self, database_path: Path, commit_id: str) -> Tuple[CheckpointPlan, RestorePlan]:
        if self._incremental_cr:
            if self._kishu_graph is None:
                raise ValueError("KishuGraph cannot be None if incremental store is enabled.")
            return self._generate_checkpoint_restore_plans(
                database_path, commit_id, self._kishu_graph.list_ancestor_commit_ids(self._kishu_graph.head())
            )
        else:
            return self._generate_checkpoint_restore_plans(database_path, commit_id, [])

    def _generate_checkpoint_restore_plans(
        self, database_path: Path, commit_id: str, parent_commit_ids: List[str]
    ) -> Tuple[CheckpointPlan, RestorePlan]:
        # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
        active_vss = self._ahg.get_active_variable_snapshots()
        for vs in active_vss:
            for varname in vs.name:
                """If manual commit made before init, pre-run cell update doesn't happen for new variables
                so we need to add them to self._id_graph_map"""
                if varname not in self._id_graph_map:
                    self._id_graph_map[varname] = get_object_state(self._user_ns[varname], {})

        # If incremental storage is enabled, retrieve list of currently stored VSes and compute VSes to
        # NOT migrate as they are already stored.
        if self._incremental_cr:
            stored_versioned_names = KishuCheckpoint(database_path).get_stored_versioned_names(parent_commit_ids)
            active_vss = [vs for vs in active_vss if VersionedName(vs.name, vs.version) not in stored_versioned_names]

        # Initialize optimizer.
        # Migration speed is set to (finite) large value to prompt optimizer to store all serializable variables.
        # Currently, a variable is recomputed only if it is unserialzable.
        optimizer = Optimizer(self._ahg, active_vss, stored_versioned_names if self._incremental_cr else None)

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.compute_plan()

        # Sort variables to migrate based on cells they were created in.
        ce_to_vs_map = defaultdict(list)
        for vs_name in vss_to_migrate:
            ce_to_vs_map[self._ahg.get_active_variable_snapshots_dict()[vs_name.name].output_ce.cell_num].append(vs_name.name)

        if self._incremental_cr:
            # Create incremental checkpoint plan using optimization results.
            checkpoint_plan = IncrementalCheckpointPlan.create(
                self._user_ns,
                database_path,
                commit_id,
                list(self._ahg.get_active_variable_snapshots_dict()[vn.name] for vn in vss_to_migrate),
            )

        else:
            # Create checkpoint plan using optimization results.
            checkpoint_plan = CheckpointPlan.create(
                self._user_ns, database_path, commit_id, list(chain.from_iterable([vs.name for vs in vss_to_migrate]))
            )

        # Create restore plan using optimization results.
        restore_plan = self._generate_restore_plan(ces_to_recompute, ce_to_vs_map, optimizer.req_func_mapping)

        return checkpoint_plan, restore_plan

    def _generate_restore_plan(
        self, ces_to_recompute: Set[int], ce_to_vs_map: Dict[int, List[VariableName]], req_func_mapping: Dict[int, Set[int]]
    ) -> RestorePlan:
        """
        Generates a restore plan based on results from the optimizer.
        @param ces_to_recompute: cell executions to rerun upon restart.
        @param ce_to_vs_map: Mapping from cell number to active variables last modified there
        @param req_func_mapping: Mapping from a cell number to all prerequisite cell numbers required
            to rerun it
        """
        restore_plan = RestorePlan()

        for ce in self._ahg.get_cell_executions():
            # Add a rerun cell restore action if the cell needs to be rerun
            if ce.cell_num in ces_to_recompute:
                restore_plan.add_rerun_cell_restore_action(ce.cell_num, ce.cell)

            # Add a load variable restore action if there are variables from the cell that needs to be stored
            if len(ce_to_vs_map[ce.cell_num]) > 0:
                restore_plan.add_load_variable_restore_action(
                    ce.cell_num,
                    list(chain.from_iterable(ce_to_vs_map[ce.cell_num])),
                    [
                        (cell_num, self._ahg.get_cell_executions_dict()[cell_num].cell)
                        for cell_num in req_func_mapping[ce.cell_num]
                    ],
                )
        return restore_plan

    def generate_incremental_restore_plan(
        self,
        database_path: Path,
        target_commit_id: CommitId,
    ) -> RestorePlan:
        if self._kishu_graph is None:
            raise ValueError("KishuGraph cannot be None if incremental store is enabled.")
        if self._kishu_commit is None:
            raise ValueError("KishuCommitGraph cannot be None if incremental store is enabled.")

        # Get active VSes in target state.
        target_commit_entry = self._kishu_commit.get_commit(target_commit_id)
        if target_commit_entry.active_vses_string is None:
            raise ValueError("No Application History Graph found for commit_id = {}".format(target_commit_id))
        target_active_vses = AHG.deserialize_active_vses(target_commit_entry.active_vses_string)

        # Get active VSes in LCA state.
        current_commit_id = self._kishu_graph.head()
        lca_commit_id = self._kishu_graph.get_lowest_common_ancestor_id(target_commit_id, current_commit_id)
        lca_commit_entry = self._kishu_commit.get_commit(lca_commit_id)
        lca_active_vses = (
            AHG.deserialize_active_vses(lca_commit_entry.active_vses_string)
            if lca_commit_entry.active_vses_string is not None
            else []
        )

        # Get parent commit IDs.
        return self._generate_incremental_restore_plan(
            database_path,
            target_active_vses,
            lca_active_vses,
            self._kishu_graph.list_ancestor_commit_ids(target_commit_id),
        )

    def _generate_incremental_restore_plan(
        self,
        database_path: Path,
        target_active_vses: List[VersionedName],
        lca_active_vses: List[VersionedName],
        target_parent_commit_ids: List[str],
    ) -> RestorePlan:
        """
        Dynamically generates an incremental restore plan. To be called at checkout time if incremental CR is enabled.
        """
        # Find currently active VSes and stored VSes that can help restoration.
        useful_vses = self._find_useful_vses(lca_active_vses, database_path, target_parent_commit_ids)

        # Compute the incremental load plan.
        opt_result = IncrementalLoadOptimizer(
            [self._ahg.get_vs_by_versioned_name(vs) for vs in target_active_vses],
            useful_vses.useful_active_vses,
            useful_vses.useful_stored_vses,
        ).compute_plan()
        # Sort the VSes to load and move by cell execution number.
        move_ce_to_vs_map: Dict[int, List[VersionedName]] = defaultdict(list)
        for versioned_name, vs in opt_result.vss_to_move.items():
            move_ce_to_vs_map[vs.output_ce.cell_num].append(versioned_name)

        load_ce_to_vs_map: Dict[int, List[VersionedName]] = defaultdict(list)
        for versioned_name, vs in opt_result.vss_to_load.items():
            load_ce_to_vs_map[vs.output_ce.cell_num].append(versioned_name)

        # Compute the incremental restore plan.
        restore_plan = RestorePlan()
        target_ces_map = {ce.cell_num: ce for ce in self._ahg.get_cell_executions()}

        for ce in self._ahg.get_cell_executions():
            # Add a rerun cell restore action if the cell needs to be rerun.
            if ce.cell_num in opt_result.ces_to_rerun:
                restore_plan.add_rerun_cell_restore_action(ce.cell_num, ce.cell)

            # Add a move variable action if variables need to be moved.
            if len(move_ce_to_vs_map[ce.cell_num]) > 0:
                restore_plan.add_move_variable_restore_action(
                    ce.cell_num,
                    self._user_ns.subset(set(chain.from_iterable([vn.name for vn in move_ce_to_vs_map[ce.cell_num]]))),
                )

            # Add a incremental load restore action if there are variables from the cell that needs to be loaded.
            if len(load_ce_to_vs_map[ce.cell_num]) > 0:
                # All loaded VSes from the same cell execution share the same fallback execution; it
                # suffices to pick any one of them.
                fallback_recomputations = [
                    (cell_num, target_ces_map[cell_num].cell)
                    for cell_num in opt_result.fallback_recomputation[load_ce_to_vs_map[ce.cell_num][0]]
                ]

                restore_plan.add_incremental_load_restore_action(
                    ce.cell_num, load_ce_to_vs_map[ce.cell_num], fallback_recomputations
                )

        return restore_plan

    def _find_useful_vses(
        self, lca_active_vses: List[VersionedName], database_path: Path, target_parent_commit_ids: List[str]
    ) -> UsefulVses:
        # If an active VS in the current session exists as an active VS in the session of the LCA,
        # the active vs can contribute toward restoration.
        lca_vses = set(lca_active_vses)
        current_vses = set(VersionedName(vs.name, vs.version) for vs in self._ahg.get_active_variable_snapshots())
        useful_active_vses = lca_vses.intersection(current_vses)

        # Get the stored VSes potentially useful for session restoration. However, if a variable is
        # currently both in the session and stored, we will never use the stored version. Discard them.
        useful_stored_vses = (
            KishuCheckpoint(database_path).get_stored_versioned_names(target_parent_commit_ids).difference(useful_active_vses)
        )

        return UsefulVses(useful_active_vses, useful_stored_vses)

    def get_ahg(self) -> AHG:
        return self._ahg

    def get_id_graph_map(self) -> Dict[str, GraphNode]:
        """
        For testing only.
        """
        return self._id_graph_map

    def serialize_active_vses(self) -> str:
        return self._ahg.serialize_active_vses()

    def replace_state(self, target_commit_entry: CommitEntry, new_user_ns: Namespace) -> None:
        """
        Replace user namespace with new_user_ns.
        Called when a checkout is performed.
        """
        # Get target AHG.
        if target_commit_entry.active_vses_string is None:
            raise ValueError("No Application History Graph found for target commit entry")
        source_active_vses = list(self.get_active_variable_snapshots_dict(self._kishu_graph.head()).keys())
        target_active_vses = list(self.get_active_variable_snapshots_dict(target_commit_entry.commit_id).keys())

        self._replace_state(source_active_vses, target_active_vses, new_user_ns)

    def _replace_state(
        self, current_active_vses: List[VersionedName], new_active_vses: List[VersionedName], new_user_ns: Namespace
    ) -> None:
        """
        Replace the current AHG's active VSes with new_active_vses and user namespace with new_user_ns.
        Called when a checkout is performed.
        """
        self._user_ns = new_user_ns

        # Update ID graphs for differing active variables.
        for varname in self._get_differing_vars_post_checkout(new_active_vses):
            self._id_graph_map[varname] = get_object_state(self._user_ns[varname], {})

        # Clear pre-run cell info.
        self._pre_run_cell_vars = set()

    def _get_differing_vars_post_checkout(
        self, current_active_vses: List[VersionedName], new_active_vses: List[VersionedName]
    ) -> Set[str]:
        """
        Finds all differing active variables between the pre and post-checkout states.
        """
        vss_diff = set(new_active_vses).difference(set(current_active_vses))
        return {name for var_snapshot in vss_diff for name in var_snapshot.name}
