from kishu.optimization.ahg import AHG, VariableSnapshot, CellExecution

import networkx as nx
from networkx.algorithms.flow import shortest_augmenting_path
import numpy as np
from typing import Tuple, List, Set, Dict


class Optimizer():
    """
        The optimizer constructs a flow graph and runs the min-cut algorithm to exactly find the best
        checkpointing configuration.
    """
    def __init__(self, ahg: AHG, active_vss: List[VariableSnapshot],
                 linked_vs_pairs: List[Tuple[VariableSnapshot, VariableSnapshot]],
                 migration_speed_bps=1) -> None:
        """
            Creates an optimizer with a migration speed estimate. The AHG and active VS fields
            must be populated prior to calling select_vss.

            @param ahg: Application History Graph.
            @param active_vss: active Variable Snapshots at time of checkpointing.
            @param linked_vs_pairs: pairs of variables sharing underlying objects. They must be migrated
                or recomputed together.
            @param migration_speed_bps: network bandwidth to storage.
        """
        self.ahg = ahg
        self.active_vss = active_vss
        self.linked_vs_pairs = linked_vs_pairs
        self.migration_speed_bps = migration_speed_bps

        # Set lookup for active VSs by name as VS objects are not hashable.
        self.active_vss_lookup = set(vs.name for vs in active_vss)

        # CEs required to recompute a variables last modified by a given CE.
        self.req_func_mapping: Dict[int, Set[int]] = {}

    def dfs_helper(self, current: str, visited: set, prerequisite_ces: set):
        """
            Perform DFS on the Application History Graph for finding the CEs required to recompute a variable.
            Args:
                current (str): Name of current nodeset.
                visited (set): Visited nodesets.
                prerequisite_ces (set): Set of CEs needing re-execution to recompute the current nodeset.
        """
        if isinstance(current, CellExecution):
            if current.cell_num in self.req_func_mapping:
                # Use memoized results if we already know prerequisite CEs of current CE.
                prerequisite_ces.update(self.req_func_mapping[current.cell_num])
            else:
                # Else, recurse into input variables of the CE.
                prerequisite_ces.add(current.cell_num)
                for vs in current.src_vss:
                    if vs.name not in self.active_vss_lookup and vs.name not in visited:
                        self.dfs_helper(vs, visited, prerequisite_ces)

        elif isinstance(current, VariableSnapshot):
            visited.add(current.name)
            if current.output_ce and current.output_ce.cell_num not in prerequisite_ces:
                self.dfs_helper(current.output_ce, visited, prerequisite_ces)

    def find_prerequisites(self):
        """
            Find the necessary (prerequisite) cell executions to rerun a cell execution.
        """
        for ce in self.ahg.cell_executions:
            # Find prerequisites only if the CE has at least 1 active output.
            if set(vs.name for vs in ce.dst_vss).intersection(self.active_vss_lookup):
                prerequisite_ces = set()
                self.dfs_helper(ce, set(), prerequisite_ces)
                self.req_func_mapping[ce.cell_num] = prerequisite_ces

    def compute_plan(self, only_migrate=True) -> Tuple[Set[str], Set[int]]:
        """
            Returns the optimal replication plan for the stored AHG consisting of
            variables to migrate and cells to rerun.
        """
        # TODO: Remove when recomputation is supported.
        if only_migrate:
            return self.active_vss_lookup, set()

        # Build prerequisite (rec) function mapping.
        self.find_prerequisites()

        # Construct flow graph for computing mincut.
        flow_graph = nx.DiGraph()

        # Add source and sink to flow graph.
        flow_graph.add_node("source")
        flow_graph.add_node("sink")

        # Add all active VSs as nodes, connect them with the source with edge capacity equal to migration cost.
        for active_vs in self.active_vss:
            flow_graph.add_node(active_vs.name)
            flow_graph.add_edge("source", active_vs.name, capacity=active_vs.size / self.migration_speed_bps)

        # Add all CEs as nodes, connect them with the sink with edge capacity equal to recomputation cost.
        for ce in self.ahg.cell_executions:
            flow_graph.add_node(ce.cell_num)
            flow_graph.add_edge(ce.cell_num, "sink", capacity=ce.cell_runtime)

        # Connect each CE with its output variables and its prerequisite CEs.
        for active_vs in self.active_vss:
            for cell_num in self.req_func_mapping[active_vs.output_ce.cell_num]:
                flow_graph.add_edge(active_vs.name, cell_num, capacity=np.inf)

        # Add constraints: overlapping variables must either be migrated or recomputed together.
        for vs_pair in self.linked_vs_pairs:
            flow_graph.add_edge(vs_pair[0].name, vs_pair[1].name, capacity=np.inf)
            flow_graph.add_edge(vs_pair[1].name, vs_pair[0].name, capacity=np.inf)

        # Prune CEs which produce no active variables to speedup computation.
        for ce in self.ahg.cell_executions:
            if flow_graph.in_degree(ce.cell_num) == 0:
                flow_graph.remove_node(ce.cell_num)

        # Solve min-cut with Ford-Fulkerson.
        cut_value, partition = nx.minimum_cut(flow_graph, "source", "sink", flow_func=shortest_augmenting_path)

        # Determine the replication plan from the partition.
        vss_to_migrate = set(partition[1]).intersection(self.active_vss_lookup)
        ces_to_recompute = set(partition[0]).intersection(set(ce.cell_num for ce in self.ahg.cell_executions))

        return vss_to_migrate, ces_to_recompute
