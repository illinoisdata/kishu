from __future__ import annotations

import numpy as np

from collections import defaultdict
from typing import Dict, Optional, Set, Tuple

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import AHG
from kishu.planning.change import find_created_and_deleted_vars, find_input_vars
from kishu.planning.idgraph import GraphNode, get_object_state
from kishu.planning.optimizer import Optimizer
from kishu.planning.plan import RestorePlan, CheckpointPlan
from kishu.planning.profiler import profile_variable_size


class CheckpointRestorePlanner:
    """
        The CheckpointRestorePlanner class holds items (e.g., AHG) relevant for creating
        the checkpoint and restoration plans during notebook runtime.
    """
    def __init__(self, user_ns: Namespace = Namespace(), ahg: AHG = AHG()) -> None:
        """
            @param user_ns  User namespace containing variables in the kernel.
        """
        self._ahg = ahg
        self._user_ns = user_ns
        self._id_graph_map: Dict[str, GraphNode] = {}
        self._pre_run_cell_vars: Set[str] = set()

        # C/R plan configs.
        self._always_recompute = False
        self._always_migrate = True

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

    def post_run_cell_update(self, code_block: Optional[str], runtime_s: Optional[float]) -> None:
        """
            Post-processing steps performed after cell execution.
            @param code_block: code of executed cell.
            @param runtime_s: runtime of cell execution.
        """
        # Find accessed variables.
        accessed_vars = (
            find_input_vars(code_block, self._pre_run_cell_vars, self._user_ns, set())
            if code_block else set()
        )

        # Find created and deleted variables.
        created_vars, deleted_vars = find_created_and_deleted_vars(self._pre_run_cell_vars,
                                                                   self._user_ns.keyset())

        # Find modified variables.
        modified_vars = set()
        for k in self._id_graph_map.keys():
            new_idgraph = get_object_state(self._user_ns[k], {})
            if not self._id_graph_map[k] == new_idgraph:
                self._id_graph_map[k] = new_idgraph
                modified_vars.add(k)

        # Update AHG.
        runtime_s = 0.0 if runtime_s is None else runtime_s

        self._ahg.update_graph(code_block, runtime_s, accessed_vars,
                               created_vars.union(modified_vars), deleted_vars)

        # Update ID graphs for newly created variables.
        for var in created_vars:
            self._id_graph_map[var] = get_object_state(self._user_ns[var], {})

    def generate_checkpoint_restore_plans(self, database_path: str, commit_id: str) -> Tuple[CheckpointPlan, RestorePlan]:

        # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
        active_vss = []
        for vs_list in self._ahg.get_variable_snapshots().values():
            if not vs_list[-1].deleted:
                active_vss.append(vs_list[-1])

        # Profile the size of each variable defined in the current session.
        for active_vs in active_vss:
            active_vs.size = profile_variable_size(self._user_ns[active_vs.name])

        # Find pairs of linked variables.
        linked_vs_pairs = []
        for active_vs1 in active_vss:
            for active_vs2 in active_vss:
                if self._id_graph_map[active_vs1.name].is_overlap(self._id_graph_map[active_vs2.name]):
                    linked_vs_pairs.append((active_vs1, active_vs2))

        # Initialize the optimizer. Migration speed is currently set to large value to prompt optimizer to store everything.
        # TODO: add overlap detection in the future.
        optimizer = Optimizer(self._ahg, active_vss, linked_vs_pairs, np.inf, only_migrate=True)

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.compute_plan()

        # Sort variables to migrate based on cells they were created in.
        ce_to_vs_map = defaultdict(list)
        for vs_name in vss_to_migrate:
            ce_to_vs_map[self._ahg.get_variable_snapshots()[vs_name][-1].output_ce.cell_num].append(vs_name)

        # Create checkpoint plan using optimization results.
        checkpoint_plan = CheckpointPlan.create(self._user_ns, database_path, commit_id, list(vss_to_migrate))

        # Create restore plan using optimization results.
        restore_plan = RestorePlan()
        for ce in self._ahg.get_cell_executions():
            if ce.cell_num in ces_to_recompute:
                restore_plan.add_rerun_cell_restore_action(ce.cell)
            if len(ce_to_vs_map[ce.cell_num]) > 0:
                restore_plan.add_load_variable_restore_action(
                        [vs_name for vs_name in ce_to_vs_map[ce.cell_num]])

        return checkpoint_plan, restore_plan

    def get_ahg(self) -> AHG:
        """
            For testing only.
        """
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
