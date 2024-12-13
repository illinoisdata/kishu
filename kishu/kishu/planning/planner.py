from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import chain, combinations
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas
from IPython.core.inputtransformer2 import TransformerManager

from kishu.exceptions import MissingHistoryError
from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import AHG, AHGUpdateInfo
from kishu.planning.idgraph import IdGraph
from kishu.planning.optimizer import IncrementalLoadOptimizer, Optimizer
from kishu.planning.plan import CheckpointPlan, IncrementalCheckpointPlan, RestorePlan
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.commit_graph import CommitId, KishuCommitGraph
from kishu.storage.config import Config
from kishu.storage.disk_ahg import CellExecution, KishuDiskAHG, VariableName, VariableSnapshot


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

    useful_active_vses: Set[VariableSnapshot]
    useful_stored_vses: Set[VariableSnapshot]


class CheckpointRestorePlanner:
    """
    The CheckpointRestorePlanner class holds items (e.g., AHG) relevant for creating
    the checkpoint and restoration plans during notebook runtime.
    """

    def __init__(
        self,
        kishu_disk_ahg: KishuDiskAHG,
        kishu_graph: KishuCommitGraph,
        user_ns: Namespace = Namespace(),
        ahg: Optional[AHG] = None,
        incremental_cr: bool = False,
    ) -> None:
        """
        @param user_ns  User namespace containing variables in the kernel.
        """
        self._ahg = ahg if ahg else AHG(kishu_disk_ahg)
        self._user_ns = user_ns
        self._id_graph_map: Dict[str, IdGraph] = {}
        self._pre_run_cell_vars: Set[str] = set()

        # C/R plan configs.
        self._incremental_cr = incremental_cr

        # Storage-related items.
        self._kishu_graph = kishu_graph
        self._kishu_disk_ahg = kishu_disk_ahg

        # Used by instrumentation to compute whether data has changed.
        self._modified_vars_structure: Set[str] = set()

    @staticmethod
    def from_existing(
        user_ns: Namespace,
        kishu_disk_ahg: KishuDiskAHG,
        kishu_graph: KishuCommitGraph,
        incremental_cr: bool,
    ) -> CheckpointRestorePlanner:
        existing_cell_executions = user_ns.ipython_in()
        if not existing_cell_executions and user_ns.keyset():
            raise MissingHistoryError()

        # Transform all magics in untracked cell code.
        untracked_cells = user_ns.ipython_in()
        transformed_untracked_cells = (
            [TransformerManager().transform_cell(cell) for cell in untracked_cells] if untracked_cells else []
        )

        return CheckpointRestorePlanner(
            kishu_disk_ahg, kishu_graph, user_ns, AHG.from_db(kishu_disk_ahg, transformed_untracked_cells), incremental_cr
        )

    def pre_run_cell_update(self) -> None:
        """
        Preprocessing steps performed prior to cell execution.
        """
        # Record variables in the user name prior to running cell if we are not in a new session.
        self._pre_run_cell_vars = self._user_ns.keyset() if self._kishu_graph.head() else set()

        # Populate missing ID graph entries.
        for var in self._user_ns.keyset():
            if var not in self._id_graph_map:
                self._id_graph_map[var] = IdGraph.from_object(self._user_ns[var])

        # Clear patched namespace trackers.
        self._user_ns.reset_accessed_vars()
        self._user_ns.reset_assigned_vars()

    def post_run_cell_update(
        self, commit_id: CommitId, code_block: Optional[str], runtime_s: Optional[float]
    ) -> ChangedVariables:
        """
        Post-processing steps performed after cell execution.
        @param code_block: code of executed cell.
        @param runtime_s: runtime of cell execution.
        """
        # Use current timestamp as version for new VSes to be created during the update.
        version = time.monotonic_ns()

        # Find accessed and assigned variables from monkey-patched namespace.
        accessed_vars = self._user_ns.accessed_vars().intersection(self._pre_run_cell_vars)
        assigned_vars = self._user_ns.assigned_vars().intersection(self._pre_run_cell_vars)

        # Find created and deleted variables
        created_vars = self._user_ns.keyset().difference(self._pre_run_cell_vars)
        deleted_vars = self._pre_run_cell_vars.difference(self._user_ns.keyset())

        # Find candidates for modified variables: a variable can only be modified if it was
        # linked with a variable that was accessed, modified, or deleted.
        touched_vars = accessed_vars.union(assigned_vars).union(deleted_vars)
        maybe_modified_vses: List[VariableSnapshot] = []
        unmodified_vses: List[VariableSnapshot] = []
        for vs in self._ahg.get_active_variable_snapshots(self._kishu_graph.head()):
            if vs.name.intersection(touched_vars):
                maybe_modified_vses.append(vs)
            else:
                unmodified_vses.append(vs)

        # Find modified variables.
        modified_vars_candidates = set(chain.from_iterable(vs.name for vs in maybe_modified_vses))
        modified_vars = set()
        for k in filter(self._user_ns.__contains__, modified_vars_candidates):
            new_idgraph = IdGraph.from_object(self._user_ns[k])

            if not self._id_graph_map[k] == new_idgraph:
                # Non-overwrite modification requires also accessing the variable.
                if self._id_graph_map[k].is_root_id_and_type_equals(new_idgraph):
                    accessed_vars.add(k)
                self._id_graph_map[k] = new_idgraph
                modified_vars.add(k)

        # Pandas dataframe dirty bit hack for ID graphs: flip the writeable flag for all newly created dataframes to false.
        if Config.get("IDGRAPH", "experimental_tracker", False):
            for var in created_vars:
                if isinstance(self._user_ns[var], pandas.DataFrame):
                    for _, col in self._user_ns[var].items():
                        col.__array__().flags.writeable = False

        # Update ID graphs for newly created variables.
        for var in created_vars:
            self._id_graph_map[var] = IdGraph.from_object(self._user_ns[var])

        # Pairs of linked variables from the previous iteration that were untouched.
        # The linked pairs created here are functionally equivalent to the ground truth in terms of union-find components.
        untouched_linked_var_pairs = []
        for vs in unmodified_vses:
            name_list = list(vs.name)
            untouched_linked_var_pairs += [(name_list[i], name_list[i + 1]) for i in range(len(name_list) - 1)]

        # Intersect ID graphs of potentially changed variables and newly created variables to find new linked variable pairs.
        new_linked_var_pairs = []
        for var1, var2 in combinations(filter(self._user_ns.__contains__, modified_vars_candidates.union(created_vars)), 2):
            if self._id_graph_map[var1].is_overlap(self._id_graph_map[var2]):
                new_linked_var_pairs.append((var1, var2))

        linked_var_pairs = untouched_linked_var_pairs + new_linked_var_pairs

        # Update AHG.
        runtime_s = 0.0 if runtime_s is None else runtime_s
        cell = TransformerManager().transform_cell(code_block) if code_block else ""
        self._ahg.update_graph(
            AHGUpdateInfo(
                self._kishu_graph.head(),
                commit_id,
                self._user_ns,
                cell,
                version,
                runtime_s,
                accessed_vars,
                self._user_ns.keyset(),
                linked_var_pairs,
                modified_vars,
                deleted_vars,
            )
        )

        # modified_vars_structure and modified_vars_value are identical after PR 396. TODO: update jupyterlab_kishu.
        return ChangedVariables(created_vars, modified_vars, modified_vars, deleted_vars)

    def generate_checkpoint_restore_plans(self, database_path: Path, commit_id: str) -> Tuple[CheckpointPlan, RestorePlan]:
        if self._incremental_cr:
            return self._generate_checkpoint_restore_plans(
                database_path, commit_id, self._kishu_graph.list_ancestor_commit_ids(self._kishu_graph.head())
            )
        else:
            return self._generate_checkpoint_restore_plans(database_path, commit_id, [])

    def _generate_checkpoint_restore_plans(
        self, database_path: Path, commit_id: str, parent_commit_ids: List[str]
    ) -> Tuple[CheckpointPlan, RestorePlan]:
        # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
        active_vss = self._ahg.get_active_variable_snapshots(commit_id)

        for varname in self._user_ns.keyset():
            """If manual commit made before init, pre-run cell update doesn't happen for new variables
            so we need to add them to self._id_graph_map"""
            if varname not in self._id_graph_map:
                self._id_graph_map[varname] = IdGraph.from_object(self._user_ns[varname])

        # If incremental storage is enabled, retrieve list of currently stored VSes and compute VSes to
        # NOT migrate as they are already stored.
        if self._incremental_cr:
            stored_versioned_names = KishuCheckpoint(database_path).get_stored_versioned_names(parent_commit_ids)
            stored_variable_snapshots = set(self._ahg.get_vs_by_versioned_names(frozenset(stored_versioned_names)))
            active_vss = set(vs for vs in active_vss if vs not in stored_variable_snapshots)

        # Initialize optimizer.
        # Migration speed is set to (finite) large value to prompt optimizer to store all serializable variables.
        # Currently, a variable is recomputed only if it is unserialzable.
        optimizer = Optimizer(self._ahg, active_vss, stored_variable_snapshots if self._incremental_cr else None)

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.compute_plan()

        if self._incremental_cr:
            # Create incremental checkpoint plan using optimization results.
            checkpoint_plan = IncrementalCheckpointPlan.create(
                self._user_ns,
                database_path,
                commit_id,
                list(vss_to_migrate),
            )

        else:
            # Create checkpoint plan using optimization results.
            checkpoint_plan = CheckpointPlan.create(
                self._user_ns, database_path, commit_id, list(chain.from_iterable([vs.name for vs in vss_to_migrate]))
            )

        # Sort variables to migrate based on cells they were created in.
        ce_to_vs_map = defaultdict(list)
        for vs_name in vss_to_migrate:
            ce_to_vs_map[self._ahg.get_vs_input_ce(vs_name)].append(vs_name.name)

        # Create restore plan using optimization results.
        restore_plan = self._generate_restore_plan(ces_to_recompute, ce_to_vs_map, optimizer.req_func_mapping)

        return checkpoint_plan, restore_plan

    def _generate_restore_plan(
        self,
        ces_to_recompute: Set[CellExecution],
        ce_to_vs_map: Dict[CellExecution, List[VariableName]],
        req_func_mapping: Dict[CellExecution, Set[CellExecution]],
    ) -> RestorePlan:
        """
        Generates a restore plan based on results from the optimizer.
        @param ces_to_recompute: cell executions to rerun upon restart.
        @param ce_to_vs_map: Mapping from cell number to active variables last modified there
        @param req_func_mapping: Mapping from a cell number to all prerequisite cell numbers required
            to rerun it
        """
        restore_plan = RestorePlan()

        for ce in self._ahg.get_all_cell_executions():
            # Add a rerun cell restore action if the cell needs to be rerun
            if ce in ces_to_recompute:
                restore_plan.add_rerun_cell_restore_action(ce.cell_num, ce.cell)

            # Add a load variable restore action if there are variables from the cell that needs to be stored
            if len(ce_to_vs_map[ce]) > 0:
                restore_plan.add_load_variable_restore_action(
                    ce.cell_num,
                    list(chain.from_iterable(ce_to_vs_map[ce])),
                    [(req_ce.cell_num, req_ce.cell) for req_ce in req_func_mapping[ce]],
                )
        return restore_plan

    def generate_incremental_restore_plan(
        self,
        database_path: Path,
        target_commit_id: CommitId,
    ) -> RestorePlan:
        # Get active VSes in target state.
        target_active_vses = self._ahg.get_active_variable_snapshots(target_commit_id)

        # Get active VSes in LCA state.
        current_commit_id = self._kishu_graph.head()
        lca_commit_id = self._kishu_graph.get_lowest_common_ancestor_id(target_commit_id, current_commit_id)
        lca_active_vses = self._ahg.get_active_variable_snapshots(lca_commit_id)

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
        target_active_vses: Set[VariableSnapshot],
        lca_active_vses: Set[VariableSnapshot],
        target_parent_commit_ids: List[str],
    ) -> RestorePlan:
        """
        Dynamically generates an incremental restore plan. To be called at checkout time if incremental CR is enabled.
        """
        # Find currently active VSes and stored VSes that can help restoration.
        useful_vses = self._find_useful_vses(lca_active_vses, database_path, target_parent_commit_ids)

        # Compute the incremental load plan.
        opt_result = IncrementalLoadOptimizer(
            self._ahg,
            target_active_vses,
            useful_vses.useful_active_vses,
            useful_vses.useful_stored_vses,
        ).compute_plan()
        # Sort the VSes to load and move by cell execution number.
        move_ce_to_vs_map: Dict[CellExecution, Set[VariableSnapshot]] = defaultdict(set)
        for vs in opt_result.vss_to_move:
            move_ce_to_vs_map[self._ahg.get_vs_input_ce(vs)].add(vs)

        load_ce_to_vs_map: Dict[CellExecution, Set[VariableSnapshot]] = defaultdict(set)
        for vs in opt_result.vss_to_load:
            load_ce_to_vs_map[self._ahg.get_vs_input_ce(vs)].add(vs)

        # Compute the incremental restore plan.
        restore_plan = RestorePlan()

        for ce in self._ahg.get_all_cell_executions():
            # Add a rerun cell restore action if the cell needs to be rerun.
            if ce in opt_result.ces_to_rerun:
                restore_plan.add_rerun_cell_restore_action(ce.cell_num, ce.cell)

            # Add a move variable action if variables need to be moved.
            if len(move_ce_to_vs_map[ce]) > 0:
                restore_plan.add_move_variable_restore_action(
                    ce.cell_num,
                    self._user_ns.subset(set(chain.from_iterable([vs.name for vs in move_ce_to_vs_map[ce]]))),
                )

            # Add a incremental load restore action if there are variables from the cell that needs to be loaded.
            if len(load_ce_to_vs_map[ce]) > 0:
                # All loaded VSes from the same cell execution share the same fallback execution; it
                # suffices to pick any one of them.
                fallback_recomputations = [
                    (req_ce.cell_num, req_ce.cell)
                    for req_ce in opt_result.fallback_recomputation[next(iter(load_ce_to_vs_map[ce]))]
                ]

                restore_plan.add_incremental_load_restore_action(ce.cell_num, load_ce_to_vs_map[ce], fallback_recomputations)

        return restore_plan

    def _find_useful_vses(
        self, lca_active_vses: Set[VariableSnapshot], database_path: Path, target_parent_commit_ids: List[str]
    ) -> UsefulVses:
        # If an active VS in the current session exists as an active VS in the session of the LCA,
        # the active vs can contribute toward restoration.
        current_vses = self._ahg.get_active_variable_snapshots(self._kishu_graph.head())
        useful_active_vses = lca_active_vses.intersection(current_vses)

        # Get the stored VSes potentially useful for session restoration. However, if a variable is
        # currently both in the session and stored, we will never use the stored version. Discard them.
        stored_vses = self._ahg.get_vs_by_versioned_names(
            frozenset(KishuCheckpoint(database_path).get_stored_versioned_names(target_parent_commit_ids))
        )
        useful_stored_vses = stored_vses.difference(useful_active_vses)

        return UsefulVses(useful_active_vses, useful_stored_vses)

    def get_ahg(self) -> AHG:
        return self._ahg

    def get_id_graph_map(self) -> Dict[str, IdGraph]:
        """
        For testing only.
        """
        return self._id_graph_map

    def replace_state(self, target_commit_id: CommitId, new_user_ns: Namespace) -> None:
        """
        Replace user namespace with new_user_ns.
        Called when a checkout is performed.
        """
        # Get target AHG.
        target_active_vses = self._ahg.get_active_variable_snapshots(target_commit_id)

        self._replace_state(target_active_vses, new_user_ns)

    def _replace_state(self, new_active_vses: Set[VariableSnapshot], new_user_ns: Namespace) -> None:
        """
        Replace the current AHG's active VSes with new_active_vses and user namespace with new_user_ns.
        Called when a checkout is performed.
        """
        self._user_ns = new_user_ns

        # Update ID graphs for differing active variables.
        for varname in self._get_differing_vars_post_checkout(new_active_vses):
            self._id_graph_map[varname] = IdGraph.from_object(self._user_ns[varname])

        # Clear pre-run cell info.
        self._pre_run_cell_vars = set()

    def _get_differing_vars_post_checkout(self, new_active_vses: Set[VariableSnapshot]) -> Set[str]:
        """
        Finds all differing active variables between the pre and post-checkout states.
        """
        pre_checkout_active_vss = self._ahg.get_active_variable_snapshots(self._kishu_graph.head())
        vss_diff = new_active_vses.difference(pre_checkout_active_vss)
        return {name for var_snapshot in vss_diff for name in var_snapshot.name}
