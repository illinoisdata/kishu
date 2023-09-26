from typing import Set, Any, Dict, List, Optional, Tuple
import numpy as np

from kishu import idgraph2 as idgraph
from kishu.optimization.ahg import AHG
from kishu.optimization.optimizer import Optimizer
from kishu.optimization.profiler import profile_variable_size
from kishu.optimization.change import find_input_vars, find_created_and_deleted_vars


class OptimizationManager:
    """
        The OptimizationManager class holds items (e.g., AHG) relevant for optimizing
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

    def pre_run_cell_update(self, pre_run_cell_vars: List[str]) -> None:
        """
            @param pre_run_cell_vars: variables in the namespace prior to cell execution.
        """
        # Record variables in the user name prior to running cell.
        self._pre_run_cell_vars = set(pre_run_cell_vars)

        # Populate missing ID graph entries.
        for var in self._ahg.variable_snapshots.keys():
            if var not in self._id_graph_map and var in self._user_ns:
                self._id_graph_map[var] = idgraph.get_object_state(self._user_ns[var], {})

    def post_run_cell_update(self, code_block: Optional[str], post_run_cell_vars: List[str],
                             start_time_ms: Optional[float], runtime_ms: Optional[float]) -> None:
        """
            @param code_block: code of executed cell.
            @param post_run_cell_vars: variables in the namespace post-cell execution.
            @param start_time_ms: start time of cell execution.
            @param runtime_ms: runtime of cell execution.
        """
        # Find accessed variables.
        if code_block:
            accessed_vars, _ = find_input_vars(code_block, self._pre_run_cell_vars,
                                               self._user_ns, set())
        else:
            accessed_vars = set()

        # Find created and deleted variables.
        post_run_cell_vars = set(post_run_cell_vars)
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

    def optimize(self) -> Tuple[Any, Any]:
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
        optimizer = Optimizer(self._ahg, active_vss, set(), np.inf)

        # Use the optimizer to compute the checkpointing configuration.
        vss_to_migrate, ces_to_recompute = optimizer.compute_plan()

        return vss_to_migrate, ces_to_recompute
