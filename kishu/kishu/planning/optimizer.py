from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx
import numpy as np
from networkx.algorithms.flow import shortest_augmenting_path

from kishu.planning.ahg import AHG, CellExecution, VariableSnapshot, VersionedName
from kishu.storage.config import Config

REALLY_FAST_BANDWIDTH_10GBPS = 10_000_000_000


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

    vss_to_move: Dict[VersionedName, VariableSnapshot] = field(default_factory=lambda: {})
    vss_to_load: Dict[VersionedName, VariableSnapshot] = field(default_factory=lambda: {})
    ces_to_rerun: Set[int] = field(default_factory=lambda: set())
    fallback_recomputation: Dict[VersionedName, Set[int]] = field(default_factory=lambda: {})


class Optimizer:
    """
    The optimizer constructs a flow graph and runs the min-cut algorithm to exactly find the best
    checkpointing and restore configurations.

    If incremental restore is enabled, the restore configuration is not used;
    it is computed on-the-fly by the GreedyIncrementalRestoreOptimizer (see below).
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
        self._optimizer_context = OptimizerContext(
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


class IncrementalLoadOptimizer:
    """
    The incremental load optimizer computes the optimal way to restore to a target session state represented
    by target_active_vss, given the current variables in the namespace useful_active_vses and stored variables
    in the database useful_stored_vses.
    """

    def __init__(
        self,
        target_active_vss: List[VariableSnapshot],
        useful_active_vses: Set[VersionedName],
        useful_stored_vses: Set[VersionedName],
    ) -> None:
        """
        Creates an optimizer with a migration speed estimate. The AHG and active VS fields
        must be populated prior to calling select_vss.

        @param ahg: Application History Graph.
        @param target_active_vss: active Variable Snapshots of the state to restore to.
        @param already_stored_vss: A List of Variable snapshots already stored in previous plans. They can be
            loaded as part of the restoration plan to save restoration time.
        """
        self.target_active_vss = target_active_vss
        self.useful_active_vses = useful_active_vses
        self.useful_stored_vses = useful_stored_vses

        # Set lookup for active VSs by name and version as VS objects are not hashable.
        self.target_active_versioned_names = {VersionedName(vs.name, vs.version) for vs in self.target_active_vss}

    def dfs_helper(
        self,
        current: Union[CellExecution, VariableSnapshot],
        visited: Set[VersionedName],
        prerequisite_ces: Set[int],
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
            prerequisite_ces.add(current.cell_num)
            for vs in current.src_vss:
                if (
                    VersionedName(vs.name, vs.version) not in self.target_active_versioned_names
                    and VersionedName(vs.name, vs.version) not in visited
                ):
                    self.dfs_helper(vs, visited, prerequisite_ces, opt_result, computing_fallback)

        elif isinstance(current, VariableSnapshot):
            visited.add(VersionedName(current.name, current.version))

            # Current VS is in the namespace.
            if VersionedName(current.name, current.version) in self.useful_active_vses:
                opt_result.vss_to_move[VersionedName(current.name, current.version)] = current

            # Current VS is stored in the DB.
            elif not computing_fallback and VersionedName(current.name, current.version) in self.useful_stored_vses:
                opt_result.vss_to_load[VersionedName(current.name, current.version)] = current

            # Else, continue checking the dependencies required to compute this VS.
            elif current.output_ce:
                self.dfs_helper(current.output_ce, visited, prerequisite_ces, opt_result, computing_fallback)

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
            prerequisite_ces: Set[int] = set()
            self.dfs_helper(vs, set(), prerequisite_ces, opt_result)
            opt_result.ces_to_rerun |= prerequisite_ces

        # For the VSes to load, find their fallback recomputations.
        for versioned_name, variable_snapshot in opt_result.vss_to_load.items():
            fallback_ces: Set[int] = set()
            self.dfs_helper(variable_snapshot, set(), fallback_ces, opt_result, computing_fallback=True)
            opt_result.fallback_recomputation[versioned_name] = fallback_ces

        return opt_result
