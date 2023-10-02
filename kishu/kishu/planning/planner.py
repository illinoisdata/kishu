from typing import Set, Any, Dict, Optional
import numpy as np
import dill
from collections import defaultdict

from kishu import idgraph2 as idgraph
from kishu.planning.ahg import AHG
from kishu.planning.optimizer import Optimizer
from kishu.planning.profiler import profile_variable_size
from kishu.planning.change import find_input_vars, find_created_and_deleted_vars
from kishu.plan import RestorePlan


class CheckpointRestorePlanner:
    """
        The CheckpointRestorePlanner class holds items (e.g., AHG) relevant for creating
        the checkpoint and restoration plans during notebook runtime.
    """
    def __init__(self, user_ns: Dict[Any, Any]) -> None:
        """
            @param user_ns  User namespace containing variables in the kernel.
        """
        self._ahg = AHG()
        self._user_ns = user_ns
        self._id_graph_map: Dict[str, idgraph.GraphNode] = {}
        self._pre_run_cell_vars: Set[str] = set()

    def pre_run_cell_update(self, pre_run_cell_vars: Set[str]) -> None:
        """
            @param pre_run_cell_vars: variables in the namespace prior to cell execution.
        """
        # Record variables in the user name prior to running cell.
        self._pre_run_cell_vars = pre_run_cell_vars

        # Populate missing ID graph entries.
        for var in self._ahg.variable_snapshots.keys():
            if var not in self._id_graph_map and var in self._user_ns:
                self._id_graph_map[var] = idgraph.get_object_state(self._user_ns[var], {})

    def post_run_cell_update(self, code_block: Optional[str], post_run_cell_vars: Set[str],
                             start_time_ms: Optional[float], runtime_ms: Optional[float]) -> None:
        """
            @param code_block: code of executed cell.
            @param post_run_cell_vars: variables in the namespace post-cell execution.
            @param start_time_ms: start time of cell execution.
            @param runtime_ms: runtime of cell execution.
        """
        # Find accessed variables.
        accessed_vars = (
            find_input_vars(code_block, self._pre_run_cell_vars, self._user_ns, set())
            if code_block else set()
        )

        # Find created and deleted variables.
        created_vars, deleted_vars = find_created_and_deleted_vars(self._pre_run_cell_vars,
                                                                   post_run_cell_vars)

        # Find modified variables.
        modified_vars = set()
        for k in self._id_graph_map.keys():
            new_idgraph = idgraph.get_object_state(self._user_ns[k], {})
            if not idgraph.compare_idgraph(self._id_graph_map[k], new_idgraph):
                self._id_graph_map[k] = new_idgraph
                modified_vars.add(k)

        # Update AHG.
        start_time = 0.0 if start_time_ms is None else float(start_time_ms * 1000)
        runtime = 0.0 if runtime_ms is None else float(runtime_ms * 1000)

        self._ahg.update_graph(code_block, runtime, start_time, accessed_vars,
                               created_vars.union(modified_vars), deleted_vars)

        # Update ID graphs for newly created variables.
        for var in created_vars:
            self._id_graph_map[var] = idgraph.get_object_state(self._user_ns[var], {})

    def generate_restore_plan(self) -> RestorePlan:
        # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
        active_vss = []
        for vs_list in self._ahg.variable_snapshots.values():
            if not vs_list[-1].deleted:
                active_vss.append(vs_list[-1])

        # Profile the size of each variable defined in the current session.
        for active_vs in active_vss:
            active_vs.size = profile_variable_size(self._user_ns[active_vs.name])

        # Initialize the optimizer. Migration speed is currently set to large value to prompt optimizer to store everything.
        # TODO: add overlap detection in the future.
        optimizer = Optimizer(self._ahg, active_vss, [], np.inf)

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.compute_plan()

        # Sort variables to migrate based on cells they were created in.
        ce_to_vs_map = defaultdict(list)
        for vs_name in vss_to_migrate:
            ce_to_vs_map[self._ahg.variable_snapshots[vs_name][-1].output_ce.cell_num].append(vs_name)

        # Create restore plan using optimization results.
        restore_plan = RestorePlan()
        for ce in self._ahg.cell_executions:
            if ce.cell_num in ces_to_recompute:
                restore_plan.add_rerun_cell_restore_action(ce.cell)
            if len(ce_to_vs_map[ce.cell_num]) > 0:
                restore_plan.add_load_variable_restore_action(
                        [vs_name for vs_name in ce_to_vs_map[ce.cell_num]])

        return restore_plan

    def get_ahg_string(self) -> str:
        """
            Returns the decoded serialized bytestring (str type) of the AHG.
            Required as the AHG is not JSON serializable by default.
        """
        return dill.dumps(self._ahg).decode('latin1')

    def replace_state(self, new_ahg_string: str, new_user_ns: Dict[Any, Any]) -> None:
        """
            Replace the current AHG with new_ahg_bytes and user namespace with new_user_ns.
            Called when a checkout is performed.
        """
        self._ahg = dill.loads(new_ahg_string.encode('latin1'))
        self._user_ns = new_user_ns

        # Also clear the old ID graphs and pre-run cell info.
        # TODO: only clear ID graphs of variables which have changed between pre and post-checkout.
        self._id_graph_map = {}
        self._pre_run_cell_vars = set()
