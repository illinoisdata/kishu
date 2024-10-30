from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
from networkx.algorithms.flow import shortest_augmenting_path

from kishu.planning.ahg import AHG, CellExecution, VariableSnapshot, VersionedName
from kishu.storage.config import Config

REALLY_FAST_BANDWIDTH_10GBPS = 10_000_000_000


@dataclass
class PlannerContext:
    """
    Optimizer-related config options.
    """

    always_recompute: bool
    always_migrate: bool
    network_bandwidth: float


class Optimizer:
    """
    The optimizer constructs a flow graph and runs the min-cut algorithm to exactly find the best
    checkpointing configuration.
    """

    def __init__(
        self, ahg: AHG, active_vss: List[VariableSnapshot], already_stored_vss: Optional[Set[VersionedName]] = None
    ) -> None:
        """
        Creates an optimizer with a migration speed estimate. The AHG and active VS fields
        must be populated prior to calling select_vss.

        @param ahg: Application History Graph.
        @param active_vss: active Variable Snapshots at time of checkpointing.
        @param already_stored_vss: A List of Variable snapshots already stored in previous plans.
            They can be loaded as part of the restoration plan to save restoration time.
        """
        self.ahg = ahg
        self.active_vss = active_vss

        # Optimizer context containing flags for optimizer parameters.
        self._optimizer_context = PlannerContext(
            always_recompute=Config.get("OPTIMIZER", "always_recompute", False),
            always_migrate=Config.get("OPTIMIZER", "always_migrate", False),
            network_bandwidth=Config.get("OPTIMIZER", "network_bandwidth", REALLY_FAST_BANDWIDTH_10GBPS),
        )

        # Set lookup for active VSs by name and version as VS objects are not hashable.
        self.active_versioned_names = {VersionedName(vs.name, vs.version) for vs in active_vss}
        self.already_stored_vss = already_stored_vss if already_stored_vss else set()

        # CEs required to recompute a variables last modified by a given CE.
        self.req_func_mapping: Dict[int, Set[int]] = {}

        if self._optimizer_context.always_migrate and self._optimizer_context.always_recompute:
            raise ValueError("always_migrate and always_recompute cannot both be True.")

    def dfs_helper(self, current: Any, visited: Set[Any], prerequisite_ces: Set[int]):
        """
        Perform DFS on the Application History Graph for finding the CEs required to recompute a variable.

        @param current: Name of current nodeset.
        @param visited: Visited nodesets.
        @param prerequisite_ces: Set of CEs needing re-execution to recompute the current nodeset.
        """
        if isinstance(current, CellExecution):
            if current.cell_num in self.req_func_mapping:
                # Use memoized results if we already know prerequisite CEs of current CE.
                prerequisite_ces.update(self.req_func_mapping[current.cell_num])
            else:
                # Else, recurse into input variables of the CE.
                prerequisite_ces.add(current.cell_num)
                for vs in current.src_vss:
                    if (
                        VersionedName(vs.name, vs.version) not in self.active_versioned_names
                        and VersionedName(vs.name, vs.version) not in self.already_stored_vss
                        and VersionedName(vs.name, vs.version) not in visited
                    ):
                        self.dfs_helper(vs, visited, prerequisite_ces)

        elif isinstance(current, VariableSnapshot):
            visited.add(VersionedName(current.name, current.version))
            if current.output_ce and current.output_ce.cell_num not in prerequisite_ces:
                self.dfs_helper(current.output_ce, visited, prerequisite_ces)

    def find_prerequisites(self):
        """
        Find the necessary (prerequisite) cell executions to rerun a cell execution.
        """
        for ce in self.ahg.get_cell_executions():
            # Find prerequisites only if the CE has at least 1 active output.
            if set(VersionedName(vs.name, vs.version) for vs in ce.dst_vss).intersection(self.active_versioned_names):
                prerequisite_ces = set()
                self.dfs_helper(ce, set(), prerequisite_ces)
                self.req_func_mapping[ce.cell_num] = prerequisite_ces

    def compute_plan(self) -> Tuple[Set[VersionedName], Set[int]]:
        """
        Returns the optimal replication plan for the stored AHG consisting of
        variables to migrate and cells to rerun.

        Test parameters (mutually exclusive):
        @param always_migrate: migrate all variables.
        @param always_recompute: rerun all cells.
        """
        # Build prerequisite (rec) function mapping.
        self.find_prerequisites()

        if self._optimizer_context.always_migrate:
            return self.active_versioned_names, set()

        if self._optimizer_context.always_recompute:
            return set(), set(ce.cell_num for ce in self.ahg.get_cell_executions())

        # Construct flow graph for computing mincut.
        flow_graph = nx.DiGraph()

        # Add source and sink to flow graph.
        flow_graph.add_node("source")
        flow_graph.add_node("sink")

        # Add all active VSs as nodes, connect them with the source with edge capacity equal to migration cost.
        for active_vs in self.active_vss:
            active_versioned_name = VersionedName(active_vs.name, active_vs.version)
            flow_graph.add_node(active_versioned_name)
            flow_graph.add_edge(
                "source", active_versioned_name, capacity=active_vs.size / self._optimizer_context.network_bandwidth
            )

        # Add all CEs as nodes, connect them with the sink with edge capacity equal to recomputation cost.
        for ce in self.ahg.get_cell_executions():
            flow_graph.add_node(ce.cell_num)
            flow_graph.add_edge(ce.cell_num, "sink", capacity=ce.cell_runtime_s)

        # Connect each CE with its output variables and its prerequisite CEs.
        for active_vs in self.active_vss:
            for cell_num in self.req_func_mapping[active_vs.output_ce.cell_num]:
                flow_graph.add_edge(VersionedName(active_vs.name, active_vs.version), cell_num, capacity=np.inf)

        # Prune CEs which produce no active variables to speedup computation.
        for ce in self.ahg.get_cell_executions():
            if flow_graph.in_degree(ce.cell_num) == 0:
                flow_graph.remove_node(ce.cell_num)

        # Solve min-cut with Ford-Fulkerson.
        cut_value, partition = nx.minimum_cut(flow_graph, "source", "sink", flow_func=shortest_augmenting_path)

        # Determine the replication plan from the partition.
        vss_to_migrate = set(partition[1]).intersection(self.active_versioned_names)
        ces_to_recompute = set(partition[0]).intersection(set(ce.cell_num for ce in self.ahg.get_cell_executions()))

        return vss_to_migrate, ces_to_recompute
