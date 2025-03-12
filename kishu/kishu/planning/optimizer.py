from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, Tuple, Union

import networkx as nx
import numpy as np
from networkx.algorithms.flow import shortest_augmenting_path

from kishu.planning.ahg import AHG
from kishu.storage.config import Config
from kishu.storage.disk_ahg import CellExecution, VariableSnapshot

REALLY_FAST_BANDWIDTH_10GBPS = 10_000_000_000


FLOW_GRAPH_SOURCE = "source"
FLOW_GRAPH_SINK = "sink"


@dataclass
class OptimizerContext:
    """
    Optimizer-related config options.
    """

    always_recompute: bool
    always_migrate: bool
    network_bandwidth: float


@dataclass
class IncrementalLoadOptimizationResult:
    """
    Optimization result for incremental load. To be packed into a RestorePlan by the planner.

    @param vss_to_move: VSes to move from the old namespace to the new namespace.
    @param vss_to_load: VSes to load from the database.
    @param ces_to_rerun: cell executions to rerun.
    @param fallback_recomputation: fallback cell executions for each VS in vss_to_load.
    """

    vss_to_move: Set[VariableSnapshot] = field(default_factory=lambda: set())
    vss_to_load: Set[VariableSnapshot] = field(default_factory=lambda: set())
    ces_to_rerun: Set[CellExecution] = field(default_factory=lambda: set())
    fallback_recomputation: Dict[VariableSnapshot, Set[CellExecution]] = field(default_factory=lambda: {})


class Optimizer:
    """
    The optimizer constructs a flow graph and runs the min-cut algorithm to exactly find the best
    checkpointing and restore configurations.

    If incremental restore is enabled, the restore configuration is not used;
    it is computed on-the-fly by the GreedyIncrementalRestoreOptimizer (see below).
    """

    def __init__(
        self, ahg: AHG, active_vss: Set[VariableSnapshot], already_stored_vss: Optional[Set[VariableSnapshot]] = None
    ) -> None:
        """
        Creates an optimizer with a migration speed estimate. The AHG and active VS fields
        must be populated prior to calling select_vss.

        @param ahg: Application History Graph.
        @param active_vss: active VersionedNames at time of checkpointing.
        @param already_stored_vss: A List of Variable snapshots already stored in previous plans.
            They can be loaded as part of the restoration plan to save restoration time.
        """
        self.ahg = ahg
        self.active_vss = set(active_vss)

        # Optimizer context containing flags for optimizer parameters.
        self._optimizer_context = OptimizerContext(
            always_recompute=Config.get("OPTIMIZER", "always_recompute", False),
            always_migrate=Config.get("OPTIMIZER", "always_migrate", True),
            network_bandwidth=Config.get("OPTIMIZER", "network_bandwidth", REALLY_FAST_BANDWIDTH_10GBPS),
        )

        # Set lookup for active VSs by name and version as VS objects are not hashable.
        self.already_stored_vss = already_stored_vss if already_stored_vss else set()

        # CEs required to recompute a variables last modified by a given CE.
        self.req_func_mapping: Dict[CellExecution, Set[CellExecution]] = {}

        if self._optimizer_context.always_migrate and self._optimizer_context.always_recompute:
            raise ValueError("always_migrate and always_recompute cannot both be True.")

    def dfs_helper(self, current: Any, visited: Set[Any], prerequisite_ces: Set[CellExecution]):
        """
        Perform DFS on the Application History Graph for finding the CEs required to recompute a variable.

        @param current: Name of current nodeset.
        @param visited: Visited nodesets.
        @param prerequisite_ces: Set of CEs needing re-execution to recompute the current nodeset.
        """
        if isinstance(current, CellExecution):
            if current in self.req_func_mapping:
                # Use memoized results if we already know prerequisite CEs of current CE.
                prerequisite_ces.update(self.req_func_mapping[current])
            else:
                # Else, recurse into input variables of the CE.
                prerequisite_ces.add(current)
                for vs in self.ahg.get_ce_input_vses(current):
                    if vs not in self.active_vss and vs not in self.already_stored_vss and vs not in visited:
                        self.dfs_helper(vs, visited, prerequisite_ces)

        elif isinstance(current, VariableSnapshot):
            visited.add(current)
            upstream_ce = self.ahg.get_vs_input_ce(current)
            if upstream_ce not in prerequisite_ces:
                self.dfs_helper(upstream_ce, visited, prerequisite_ces)

    def find_prerequisites(self):
        """
        Find the necessary (prerequisite) cell executions to rerun a cell execution.
        """
        for ce in self.ahg.get_all_cell_executions():
            # Find prerequisites only if the CE has at least 1 active output.
            if set(self.ahg.get_ce_output_vses(ce)).intersection(self.active_vss):
                prerequisite_ces = set()
                self.dfs_helper(ce, set(), prerequisite_ces)
                self.req_func_mapping[ce] = prerequisite_ces

    def compute_plan(self) -> Tuple[Set[VariableSnapshot], Set[CellExecution]]:
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
            return self.active_vss, set()

        if self._optimizer_context.always_recompute:
            return set(), set(self.ahg.get_all_cell_executions())

        # Construct flow graph for computing mincut.
        flow_graph = nx.DiGraph()

        # Add source and sink to flow graph.
        flow_graph.add_node(FLOW_GRAPH_SOURCE)
        flow_graph.add_node(FLOW_GRAPH_SINK)

        # Add all active VSs as nodes, connect them with the source with edge capacity equal to migration cost.
        for active_vs in self.active_vss:
            flow_graph.add_node(active_vs)
            flow_graph.add_edge(
                FLOW_GRAPH_SOURCE,
                active_vs,
                capacity=active_vs.size / self._optimizer_context.network_bandwidth,
            )

        # Add all CEs as nodes, connect them with the sink with edge capacity equal to recomputation cost.
        for ce in self.ahg.get_all_cell_executions():
            flow_graph.add_node(ce)
            flow_graph.add_edge(ce, FLOW_GRAPH_SINK, capacity=ce.cell_runtime_s)

        # Connect each CE with its output variables and its prerequisite CEs.
        for active_vs in self.active_vss:
            for ce in self.req_func_mapping[self.ahg.get_vs_input_ce(active_vs)]:
                flow_graph.add_edge(active_vs, ce, capacity=np.inf)

        # Prune CEs which produce no active variables to speedup computation.
        for ce in self.ahg.get_all_cell_executions():
            if flow_graph.in_degree(ce) == 0:
                flow_graph.remove_node(ce)

        # Solve min-cut with Ford-Fulkerson.
        cut_value, partition = nx.minimum_cut(
            flow_graph, FLOW_GRAPH_SOURCE, FLOW_GRAPH_SINK, flow_func=shortest_augmenting_path
        )

        # Determine the replication plan from the partition.
        vss_to_migrate = set(partition[1]).intersection(self.active_vss)
        ces_to_recompute = set(partition[0]).intersection(set(self.ahg.get_all_cell_executions()))

        return vss_to_migrate, ces_to_recompute


class IncrementalLoadOptimizer:
    """
    The incremental load optimizer computes the optimal way to restore to a target session state represented
    by target_active_vss, given the current variables in the namespace useful_active_vses and stored variables
    in the database useful_stored_vses.
    """

    def __init__(
        self,
        ahg: AHG,
        target_active_vss: Set[VariableSnapshot],
        useful_active_vses: Set[VariableSnapshot],
        useful_stored_vses: Set[VariableSnapshot],
    ) -> None:
        """
        Creates an optimizer with a migration speed estimate. The AHG and active VS fields
        must be populated prior to calling select_vss.

        @param ahg: Application History Graph.
        @param target_active_vss: active Variable Snapshots of the state to restore to.
        @param already_stored_vss: A List of Variable snapshots already stored in previous plans. They can be
            loaded as part of the restoration plan to save restoration time.
        """
        self.ahg = ahg
        self.target_active_vss = target_active_vss
        self.useful_active_vses = useful_active_vses
        self.useful_stored_vses = useful_stored_vses

    def dfs_helper(
        self,
        current: Union[CellExecution, VariableSnapshot],
        visited: Set[VariableSnapshot],
        prerequisite_ces: Set[CellExecution],
        opt_result: IncrementalLoadOptimizationResult,
        computing_fallback=False,
    ):
        """
        Perform DFS on the Application History Graph for finding the CEs required to recompute a variable.

        @param current: Name of current nodeset.
        @param visited: Visited nodesets.
        @param prerequisite_ces: Set of CEs needing re-execution to recompute the current nodeset.
        @param computing_fallback: whether this DFS run is for finding fallback recomputation. If yes, skip using
            any VSes stored in the DB (as they are the main point of failure).
        """
        if isinstance(current, CellExecution):
            prerequisite_ces.add(current)
            for vs in self.ahg.get_ce_input_vses(current):
                if vs not in self.target_active_vss and vs not in visited:
                    self.dfs_helper(vs, visited, prerequisite_ces, opt_result, computing_fallback)

        elif isinstance(current, VariableSnapshot):
            visited.add(current)

            # Current VS is in the namespace.
            if current in self.useful_active_vses:
                opt_result.vss_to_move.add(current)

            # Current VS is stored in the DB.
            elif not computing_fallback and current in self.useful_stored_vses:
                opt_result.vss_to_load.add(current)

            # Else, continue checking the dependencies required to compute this VS.
            else:
                self.dfs_helper(self.ahg.get_vs_input_ce(current), visited, prerequisite_ces, opt_result, computing_fallback)

    def compute_plan(self) -> IncrementalLoadOptimizationResult:
        """
        Returns the optimal replication plan for the stored AHG consisting of
        variables to migrate and cells to rerun.

        Test parameters (mutually exclusive):
        @param always_migrate: migrate all variables.
        @param always_recompute: rerun all cells.
        """
        opt_result = IncrementalLoadOptimizationResult()

        # Greedily find the cells to rerun, VSes to move and VSes to load for each active VS in the target state.
        for vs in self.target_active_vss:
            prerequisite_ces: Set[CellExecution] = set()
            self.dfs_helper(vs, set(), prerequisite_ces, opt_result)
            opt_result.ces_to_rerun |= prerequisite_ces

        # For the VSes to load, find their fallback recomputations.
        for vs in opt_result.vss_to_load:
            fallback_ces: Set[CellExecution] = set()
            self.dfs_helper(vs, set(), fallback_ces, opt_result, computing_fallback=True)
            opt_result.fallback_recomputation[vs] = fallback_ces

        return opt_result
