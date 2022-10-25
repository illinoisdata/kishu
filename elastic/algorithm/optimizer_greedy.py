#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from elastic.algorithm.selector import Selector
from elastic.core.graph.node_set import NodeSet
from elastic.core.graph.node_set import NodeSetType
import networkx as nx
import numpy as np


class OptimizerGreedy(Selector):
    """
        The greedy optimizer uses greedy submodular optimization to compute a checkpointing configuration.
    """

    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

        # Augmented computation graph
        self.compute_graph = None

        # A node set is active if all of its VSs are active.
        self.active_node_sets = set()

        # Unique index number assigned to node sets to speedup lookup
        self.idx_to_node_set = {}

        # OEs required to recompute a give nodeset.
        self.recomputation_oes = {}

        self.idx = 0

    def get_new_idx(self) -> int:
        """
            Get a new index number to add to compute graph.
        """
        idx = self.idx
        self.idx += 1
        return idx

    def dfs(self, current: str, visited: set, recompute_oes: str):
        """
            DFS helper for finding the OEs required to recompute a node set.
            Args:
                current (str): Name of current nodeset.
                visited (set): Visited nodesets.
                recompute_oes (set): Set of OEs needing re-execution to recompute the cirremt nodeset.
        """
        visited.add(current)
        for parent in self.compute_graph.predecessors(current):
            recompute_oes.add((parent, current))
            if parent not in self.active_node_sets and parent not in visited:
                self.dfs(parent, visited, recompute_oes)

    def construct_graph(self):
        """
            Construct the augmented dependency graph.
        """
        self.compute_graph = nx.DiGraph()
        self.active_vss = set(self.active_vss)
        srcs = []
        dsts = []

        for oe in self.dependency_graph.operation_events:
            # Add source and destination node sets to graph
            src_idx = self.get_new_idx()
            dst_idx = self.get_new_idx()

            self.compute_graph.add_node(src_idx)
            self.compute_graph.add_node(dst_idx)

            self.idx_to_node_set[src_idx] = oe.src
            self.idx_to_node_set[dst_idx] = oe.dst

            srcs.append(src_idx)
            dsts.append(dst_idx)

            self.compute_graph.add_edge(src_idx, dst_idx, weight=oe.cell_runtime)

            # The output node set has a nonempty strict subset of active nodes
            active_vs_subset = set(oe.dst.vs_list).intersection(self.active_vss)
            if active_vs_subset and active_vs_subset != set(oe.dst.vs_list):
                dst_active_subset_idx = self.get_new_idx()
                self.compute_graph.add_node(dst_active_subset_idx)
                self.idx_to_node_set[dst_active_subset_idx] = NodeSet(list(active_vs_subset), NodeSetType.DUMMY)
                dsts.append(dst_active_subset_idx)
                self.compute_graph.add_edge(dst_idx, dst_active_subset_idx, weight=0)

        # Augment compute graph with edges between overlapping destination and source sets
        for dst in dsts:
            for src in srcs:
                if set(self.idx_to_node_set[dst].vs_list).intersection(
                        set(self.idx_to_node_set[src].vs_list)):
                    self.compute_graph.add_edge(dst, src, weight=0)

        # Find active node sets consisting entirely of active nodes
        for idx in self.compute_graph.nodes():
            if set(self.idx_to_node_set[idx].vs_list).issubset(self.active_vss) \
                    and len(set(self.idx_to_node_set[idx].vs_list)) > 0:
                self.active_node_sets.add(idx)

        # Find edges required to recompute each node set given all active node sets are migrated
        for idx in self.compute_graph.nodes():
            recompute_oes = set()
            self.dfs(idx, set(), recompute_oes)
            self.recomputation_oes[idx] = recompute_oes

    def compute_migration_cost(self, node_sets: set) -> float:
        """
            Compute the total cost to migrate the unique VSs in the specified node sets.
            Args:
                node_sets (set): set of nodesets to migrate.
        """
        migrate_vss = set().union(*[self.idx_to_node_set[i].vs_list for i in node_sets])
        return sum([i.size for i in migrate_vss]) / self.migration_speed_bps

    def compute_recomputation_cost(self, node_sets: set) -> float:
        """
            Compute the total cost to re-execute the unique OEs to recompute specified node sets.
            Args:
                node_sets (set): set of nodesets to recompute.
        """
        recompute_oes = set().union(*[self.recomputation_oes[i] for i in node_sets])
        return sum([self.compute_graph.get_edge_data(*i)["weight"] for i in recompute_oes])

    def total_cost(self, migrated_node_sets: set) -> float:
        """
            Compute the total migration and recomputation cost of a checkpointing configuration.
            Args:
                migrated_node_sets (set): set of nodesets to migrate.
        """
        return self.compute_migration_cost(migrated_node_sets) + \
               self.compute_recomputation_cost(
                   self.active_node_sets.difference(migrated_node_sets))

    def select_vss(self) -> set:
        self.construct_graph()

        # start with migrating all, greedily un-migrate node sets
        migrated_node_sets = set()
        for node_set in self.active_node_sets:
            migrated_node_sets.add(node_set)

        while True:
            # Find best nodeset to un-migrate
            best_decrease = -np.inf
            best_set = None
            current_score = self.total_cost(migrated_node_sets)
            for node_set in migrated_node_sets:
                decrease = current_score - self.total_cost(
                    migrated_node_sets.difference({node_set}))
                if decrease > best_decrease:
                    best_decrease = decrease
                    best_set = node_set

            # Stop if un-migrating nodesets will not further decrease cost
            if best_decrease < 0:
                break
            migrated_node_sets = migrated_node_sets.difference({best_set})

        # VSs to migrate as the union of the VSs in the nodesets to migrate.
        vss_to_migrate = set()
        for i in list(migrated_node_sets):
            for vs in self.idx_to_node_set[i].vs_list:
                vss_to_migrate.add(vs)
        return vss_to_migrate
