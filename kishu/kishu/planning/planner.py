from __future__ import annotations

import time

from collections import defaultdict
from dataclasses import dataclass
from itertools import chain, combinations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from kishu.jupyter.namespace import Namespace

from kishu.planning.ahg import AHG, VersionedName, VersionedNameContext
from kishu.planning.idgraph import GraphNode, get_object_state, value_equals
from kishu.planning.optimizer import IncrementalLoadOptimizer, Optimizer
from kishu.planning.plan import CheckpointPlan, IncrementalCheckpointPlan, RestorePlan
from kishu.planning.profiler import profile_variable_size
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.config import Config


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
        self._incremental_cr = Config.get('PLANNER', 'incremental_cr', False)

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
        for var in self._ahg.get_variable_names():
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

        # Update ID graphs for newly created variables.
        for var in created_vars:
            self._id_graph_map[var] = get_object_state(self._user_ns[var], {})

        # Find pairs of linked variables.
        linked_var_pairs = []
        for x, y in combinations(filter(self._user_ns.__contains__, self._id_graph_map.keys()), 2):
            if self._id_graph_map[x].is_overlap(self._id_graph_map[y]):
                linked_var_pairs.append((x, y))

        # Update AHG.
        runtime_s = 0.0 if runtime_s is None else runtime_s

        self._ahg.update_graph(code_block, version, runtime_s, accessed_vars, self._user_ns.keyset(), linked_var_pairs,
                               modified_vars_structure, deleted_vars)

        return ChangedVariables(created_vars, modified_vars_value, modified_vars_structure, deleted_vars)

    def generate_checkpoint_restore_plans(
        self,
        database_path: str,
        commit_id: str,
        parent_commit_ids: Optional[List[str]]=None
    ) -> Tuple[CheckpointPlan, RestorePlan]:
        # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
        active_vss = self._ahg.get_active_variable_snapshots()
        for vs in active_vss:
            for varname in vs.name:
                """If manual commit made before init, pre-run cell update doesn't happen for new variables
                so we need to add them to self._id_graph_map"""
                if varname not in self._id_graph_map:
                    self._id_graph_map[varname] = get_object_state(self._user_ns[varname], {})

        # If incremental storage is enabled, retrieve list of currently stored VSes in parent commits and compute VSes to
        # NOT migrate as they are already stored.
        if self._incremental_cr:
            if parent_commit_ids is None:
                raise ValueError("parent_commit_ids cannot be none if incremental CR is enabled.")
            stored_versioned_names = KishuCheckpoint(database_path).get_stored_versioned_names(parent_commit_ids)
            active_vss = [vs for vs in active_vss if
                          VersionedName(vs.name, vs.version) not in stored_versioned_names.keys()]

        # Profile the size of each variable defined in the current session.
        for active_vs in active_vss:
            if len(active_vs.name) == 1:
                active_vs.size = profile_variable_size([self._user_ns[varname] for varname in active_vs.name])
            else:
                active_vs.size = profile_variable_size([self._user_ns[varname] for varname in active_vs.name][0])
            print("size:", active_vs.name, active_vs.size)

        # Initialize optimizer.
        # Migration speed is set to (finite) large value to prompt optimizer to store all serializable variables.
        # Currently, a variable is recomputed only if it is unserialzable.
        optimizer = Optimizer(
            self._ahg,
            active_vss,
            stored_versioned_names if self._incremental_cr else None
        )

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.compute_plan()
        print("vss_to_migrate:", vss_to_migrate)
        print("ces_to_recompute:", ces_to_recompute)

        # Sort variables to migrate based on cells they were created in.
        ce_to_vs_map = defaultdict(list)
        for vs_name in vss_to_migrate:
            ce_to_vs_map[self._ahg.get_active_variable_snapshots_dict()[vs_name].output_ce.cell_num].extend(list(vs_name))

        if self._incremental_cr:
            # Create incremental checkpoint plan using optimization results.
            checkpoint_plan = IncrementalCheckpointPlan.create(
                self._user_ns,
                database_path,
                commit_id,
                list(self._ahg.get_active_variable_snapshots_dict()[vs_name] for vs_name in vss_to_migrate)
            )
            print("incremental checkpoint:", vss_to_migrate)
        else:
            # Create checkpoint plan using optimization results.
            checkpoint_plan = CheckpointPlan.create(self._user_ns, database_path, commit_id,
                                                    list(chain.from_iterable(vss_to_migrate)))

        # Create restore plan using optimization results.
        restore_plan = self._generate_restore_plan(ces_to_recompute, ce_to_vs_map, optimizer.req_func_mapping)

        return checkpoint_plan, restore_plan

    def _generate_restore_plan(
        self,
        ces_to_recompute: Set[int],
        ce_to_vs_map: Dict[int, List[str]],
        req_func_mapping: Dict[int, Set[int]]
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
                        [(cell_num, ce_dict[cell_num].cell) for cell_num in req_func_mapping[ce.cell_num]])
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

    def restore_state(
        self,
        new_ahg_string: str,
        restore_plan: RestorePlan,
        database_path: str,
        commit_id: str,
        parent_commit_ids: Optional[List[str]]=None,
        lca_ahg_string: Optional[str] = None
    ) -> Namespace:
        """
            Replace the current AHG with new_ahg_bytes and user namespace with new_user_ns.
            Called when a checkout is performed.
        """
        if not self._incremental_cr:
            # Regular restore: use the provided restore plan.
            result_ns = restore_plan.run(database_path, commit_id)
            self._ahg = AHG.deserialize(new_ahg_string)
        else:
            # Incremental restore: dynamically recompute the restore plan.
            if lca_ahg_string is None:
                raise ValueError("lca_ahg_string cannot be None if incremental CR is enabled.")
    
            if parent_commit_ids is None:
                raise ValueError("parent_commit_ids cannot be None if incremental CR is enabled.")

            target_ahg = AHG.deserialize(new_ahg_string)
            lca_ahg = AHG.deserialize(lca_ahg_string)
            incremental_restore_plan = self.generate_incremental_restore_plan(
                target_ahg,
                lca_ahg,
                database_path,
                parent_commit_ids
            )
            # run the restore plan.
            result_ns = incremental_restore_plan.run(database_path, commit_id)
            print("result keyset:", result_ns.keyset())
            self._ahg = target_ahg

        self._user_ns = result_ns

        # Also clear the old ID graphs and pre-run cell info.
        # TODO: only clear ID graphs of variables which have changed between pre and post-checkout.
        self._id_graph_map = {}
        self._pre_run_cell_vars = set()

        return result_ns

    def generate_incremental_restore_plan(
        self,
        target_ahg: AHG,
        lca_ahg: AHG,
        database_path: str,
        parent_commit_ids: List[str]
    ) -> RestorePlan:
        # Get the target active VSes to restore.
        target_active_vss = target_ahg.get_active_variable_snapshots()
        print("target_active_vss:", [(vs.name, vs.version) for vs in target_active_vss])

        # Find useful VSes for session restoration.
        useful_active_vses, useful_stored_vses = self._find_useful_vses(lca_ahg, database_path, parent_commit_ids)
        print("useful_active_vses:", useful_active_vses)
        print("useful_stored_vses:", set(useful_stored_vses.keys()))

        # Compute the incremental load plan.
        opt = IncrementalLoadOptimizer(target_ahg, target_active_vss, useful_active_vses, useful_stored_vses)
        vss_to_move, vss_to_load, ces_to_recompute = opt.compute_plan()

        # Sort the VSes to load and move by cell execution number.
        move_ce_to_vs_map: Dict[int, List[FrozenSet[str]]] = defaultdict(list)
        for versioned_name, vs in vss_to_move.items():
            move_ce_to_vs_map[vs.output_ce.cell_num].append(versioned_name.name)

        load_ce_to_vs_map: Dict[int, List[Tuple[VersionedName, VersionedNameContext]]] = defaultdict(list)
        for k, v in vss_to_load.items():
            load_ce_to_vs_map[v[0].output_ce.cell_num].append((k, v[1]))

        incremental_restore_plan = self._generate_incremental_restore_plan_helper(
            ces_to_recompute,
            move_ce_to_vs_map,
            load_ce_to_vs_map,
            opt.fallback_recomputation
        )
        return incremental_restore_plan

    def _find_useful_vses(
        self,
        lca_ahg: AHG,
        database_path: str,
        parent_commit_ids: List[str]
    ) -> Tuple[Set[VersionedName], Dict[VersionedName, VersionedNameContext]]:
        # If an active VS in the current session exists as an active VS in the session of the LCA,
        # the active vs can contribute toward restoration.
        lca_vses = set(VersionedName(vs.name, vs.version) for vs in lca_ahg.get_active_variable_snapshots())
        current_vses = set(VersionedName(vs.name, vs.version) for vs in self._ahg.get_active_variable_snapshots())
        useful_active_vses = lca_vses.intersection(current_vses)

        # Get the stored VSes potentially useful for sessionr restoration. However, if a variable is 
        # currently both in the session and stored, we will never use the stored version. Discard them.
        useful_stored_vses = KishuCheckpoint(database_path).get_stored_versioned_names(parent_commit_ids)
        useful_stored_vses = {k:v for k,v in useful_stored_vses.items() if k not in useful_active_vses}

        return useful_active_vses, useful_stored_vses

    def _generate_incremental_restore_plan_helper(
        self,
        ces_to_recompute: Set[int],
        move_ce_to_vs_map: Dict[int, List[FrozenSet[str]]],
        load_ce_to_vs_map: Dict[int, List[Tuple[VersionedName, VersionedNameContext]]],
        fallback_recomputation: Dict[VersionedName, Set[int]]
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
                print("add rerun cell action:", ce.cell_num, ce.cell)
                restore_plan.add_rerun_cell_restore_action(ce.cell_num, ce.cell)

            # Add a move variable action if variables need to be moved.
            if len(move_ce_to_vs_map[ce.cell_num]) > 0:
                print("add move variable action:", ce.cell_num, set(chain.from_iterable(move_ce_to_vs_map[ce.cell_num])))
                restore_plan.add_move_variable_restore_action(
                    ce.cell_num,
                    self._user_ns.subset(set(chain.from_iterable(move_ce_to_vs_map[ce.cell_num])))
                )

            # Add a incremental load restore action if there are variables from the cell that needs to be stored
            if len(load_ce_to_vs_map[ce.cell_num]) > 0:
                print("add load variable action:", ce.cell_num, [i[0] for i in load_ce_to_vs_map[ce.cell_num]])
                restore_plan.add_incremental_load_restore_action(
                    ce.cell_num,
                    load_ce_to_vs_map[ce.cell_num],
                    [(cell_num, ce_dict[cell_num].cell) for cell_num in fallback_recomputation[load_ce_to_vs_map[ce.cell_num][0][0]]])
        return restore_plan
