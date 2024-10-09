from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import AHG, VariableSnapshot, VersionedName, VsConnectedComponents
from kishu.planning.idgraph import GraphNode, get_object_state, value_equals
from kishu.planning.optimizer import Optimizer
from kishu.planning.plan import CheckpointPlan, IncrementalCheckpointPlan, RestorePlan
from kishu.planning.profiler import profile_variable_size
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.config import Config


@dataclass
class PlannerContext:
    """
    Planner-related config options.
    """

    incremental_store: bool
    incremental_load: bool  # Not used yet


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


class CheckpointRestorePlanner:
    """
    The CheckpointRestorePlanner class holds items (e.g., AHG) relevant for creating
    the checkpoint and restoration plans during notebook runtime.
    """

    def __init__(self, user_ns: Namespace = Namespace(), ahg: Optional[AHG] = None) -> None:
        """
        @param user_ns  User namespace containing variables in the kernel.
        """
        self._ahg = ahg if ahg else AHG()
        self._user_ns = user_ns
        self._id_graph_map: Dict[str, GraphNode] = {}
        self._pre_run_cell_vars: Set[str] = set()

        # C/R plan configs.
        self._planner_context = PlannerContext(
            incremental_store=Config.get("PLANNER", "incremental_store", False),
            incremental_load=Config.get("PLANNER", "incremental_load", False),  # Not used yet
        )

        # Used by instrumentation to compute whether data has changed.
        self._modified_vars_structure: Set[str] = set()

    @staticmethod
    def from_existing(user_ns: Namespace) -> CheckpointRestorePlanner:
        return CheckpointRestorePlanner(user_ns, AHG.from_existing(user_ns))

    def pre_run_cell_update(self) -> None:
        """
        Preprocessing steps performed prior to cell execution.
        """
        # Record variables in the user name prior to running cell.
        self._pre_run_cell_vars = self._user_ns.keyset()

        # Populate missing ID graph entries.
        for var in self._ahg.get_variable_snapshots().keys():
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

        # Find created and deleted variables.
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

        # Update AHG.
        runtime_s = 0.0 if runtime_s is None else runtime_s

        self._ahg.update_graph(
            code_block, version, runtime_s, accessed_vars, created_vars.union(modified_vars_structure), deleted_vars
        )

        # Update ID graphs for newly created variables.
        for var in created_vars:
            self._id_graph_map[var] = get_object_state(self._user_ns[var], {})

        return ChangedVariables(created_vars, modified_vars_value, modified_vars_structure, deleted_vars)

    def incremental_store_adjustment(
        self,
        active_vss: List[VariableSnapshot],
        linked_vs_pairs: List[Tuple[VariableSnapshot, VariableSnapshot]],
        database_path: str,
    ) -> Tuple[List[VariableSnapshot], Set[VersionedName]]:
        """
        Adjust the active variables and optimizer settings according to already stored variables if incremental
        computation is enabled.
        """
        # Currently stored VSes
        stored_vs_connected_components = KishuCheckpoint(database_path).get_stored_connected_components()
        stored_vses = stored_vs_connected_components.get_versioned_names()

        # VSes in session state
        current_vs_connected_components = VsConnectedComponents.create_from_vses(active_vss, linked_vs_pairs)

        # If a connected component of VSes in the current session state is a subset of an already stored
        # connected component, we can skip storing it.
        stored_active_vses: Set[VersionedName] = set()
        for current_component in current_vs_connected_components.get_connected_components():
            if stored_vs_connected_components.contains_component(current_component):
                stored_active_vses.update(set(current_component))

        # Return the active VSes we need to store and the already stored (not necessarily active) VSes
        return [vs for vs in active_vss if VersionedName(vs.name, vs.version) not in stored_active_vses], stored_vses

    def generate_checkpoint_restore_plans(self, database_path: str, commit_id: str) -> Tuple[CheckpointPlan, RestorePlan]:
        # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
        active_vss = []
        for *_, latest_vs in self._ahg.get_variable_snapshots().values():
            if not latest_vs.deleted:
                """If manual commit made before init, pre-run cell update doesn't happen for new variables
                so we need to add them to self._id_graph_map"""
                if latest_vs.name not in self._id_graph_map:
                    self._id_graph_map[latest_vs.name] = get_object_state(self._user_ns[latest_vs.name], {})
                active_vss.append(latest_vs)

        # Profile the size of each variable defined in the current session.
        for active_vs in active_vss:
            active_vs.size = profile_variable_size(self._user_ns[active_vs.name])

        # Find pairs of linked variables.
        linked_vs_pairs = []
        for active_vs1, active_vs2 in combinations(active_vss, 2):
            if self._id_graph_map[active_vs1.name].is_overlap(self._id_graph_map[active_vs2.name]):
                linked_vs_pairs.append((active_vs1, active_vs2))

        # If incremental storage is enabled, retrieve list of currently stored VSes and compute VSes to
        # NOT migrate as they are already stored.
        if self._planner_context.incremental_store:
            active_vss, already_stored_vses = self.incremental_store_adjustment(active_vss, linked_vs_pairs, database_path)

        # Initialize optimizer.
        # Migration speed is set to (finite) large value to prompt optimizer to store all serializable variables.
        # Currently, a variable is recomputed only if it is unserialzable.
        optimizer = Optimizer(
            self._ahg, active_vss, linked_vs_pairs, already_stored_vses if self._planner_context.incremental_store else None
        )

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.compute_plan()

        # Sort variables to migrate based on cells they were created in.
        ce_to_vs_map = defaultdict(list)
        for vs_name in vss_to_migrate:
            ce_to_vs_map[self._ahg.get_variable_snapshots()[vs_name][-1].output_ce.cell_num].append(vs_name)

        if self._planner_context.incremental_store:
            # Find linked variables which are migrated which form connected components.
            vs_connected_components_to_store = VsConnectedComponents.create_from_vses(
                [vs for vs in active_vss if vs.name in vss_to_migrate],
                [(vs1, vs2) for vs1, vs2 in linked_vs_pairs if vs1.name in vss_to_migrate and vs2.name in vss_to_migrate],
            )

            # Create incremental checkpoint plan using optimization results.
            checkpoint_plan = IncrementalCheckpointPlan.create(
                self._user_ns, database_path, commit_id, vs_connected_components_to_store
            )
        else:
            # Create checkpoint plan using optimization results.
            checkpoint_plan = CheckpointPlan.create(self._user_ns, database_path, commit_id, list(vss_to_migrate))

        # Create restore plan using optimization results.
        restore_plan = self._generate_restore_plan(ces_to_recompute, ce_to_vs_map, optimizer.req_func_mapping)

        return checkpoint_plan, restore_plan

    def _generate_restore_plan(
        self, ces_to_recompute: Set[int], ce_to_vs_map: Dict[int, List[str]], req_func_mapping: Dict[int, Set[int]]
    ) -> RestorePlan:
        """
        Generates a restore plan based on results from the optimizer.
        @param ces_to_recompute: cell executions to rerun upon restart.
        @param ce_to_vs_map: Mapping from cell number to active variables last modified there
        @param req_func_mapping: Mapping from a cell number to all prerequisite cell numbers required
            to rerun it
        """
        restore_plan = RestorePlan()

        ce_dict = {ce.cell_num: ce for ce in self._ahg.get_cell_executions()}

        for ce in self._ahg.get_cell_executions():
            # Add a rerun cell restore action if the cell needs to be rerun
            if ce.cell_num in ces_to_recompute:
                restore_plan.add_rerun_cell_restore_action(ce.cell_num, ce.cell)

            # Add a load variable restore action if there are variables from the cell that needs to be stored
            if len(ce_to_vs_map[ce.cell_num]) > 0:
                restore_plan.add_load_variable_restore_action(
                    ce.cell_num,
                    [vs_name for vs_name in ce_to_vs_map[ce.cell_num]],
                    [(cell_num, ce_dict[cell_num].cell) for cell_num in req_func_mapping[ce.cell_num]],
                )
        return restore_plan

    def get_ahg(self) -> AHG:
        return self._ahg

    def get_id_graph_map(self) -> Dict[str, GraphNode]:
        """
        For testing only.
        """
        return self._id_graph_map

    def serialize_ahg(self) -> str:
        """
        Returns the decoded serialized bytestring (str type) of the AHG.
        Required as the AHG is not JSON serializable by default.
        """
        return self._ahg.serialize()

    def replace_state(self, new_ahg_string: str, new_user_ns: Namespace) -> None:
        """
        Replace the current AHG with new_ahg_bytes and user namespace with new_user_ns.
        Called when a checkout is performed.
        """
        self._ahg = AHG.deserialize(new_ahg_string)
        self._user_ns = new_user_ns

        # Also clear the old ID graphs and pre-run cell info.
        # TODO: only clear ID graphs of variables which have changed between pre and post-checkout.
        self._id_graph_map = {}
        self._pre_run_cell_vars = set()
