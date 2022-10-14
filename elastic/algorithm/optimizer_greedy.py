#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from algorithm.selector import Selector
from core.graph.node_set import NodeSet
import networkx as nx
import numpy as np


class OptimizerGreedy(Selector):

    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

        # Augmented computation graph
        self.compute_graph = None

        # A node set is active if all of its nodes are active.
        self.active_node_sets = set()

        # Unique index number assigned to node sets to speedup lookup
        self.idx_to_node_set = {}

        # Edges required to recompute a give nodeset.
        self.recomputation_edges = {}

        self.idx = 0

    # Get a new index number to add to compute graph
    def get_new_idx(self):
        idx = self.idx
        self.idx += 1
        return idx

    # DFS helper for finding the edges required to recompute a node set
    def dfs(self, current, visited, recompute_edges):
        visited.add(current)
        for parent in self.compute_graph.predecessors(current):
            recompute_edges.add((parent, current))
            if parent not in self.active_node_sets and parent not in visited:
                self.dfs(parent, visited, recompute_edges)

    # Construct compute graph from node sets
    def construct_graph(self):
        self.active_nodes = set(self.active_nodes)
        self.compute_graph = nx.DiGraph()
        srcs = []
        dsts = []

        for edge in self.dependency_graph.edges:
            # Add source and destination node sets to graph
            src_idx = self.get_new_idx()
            dst_idx = self.get_new_idx()

            self.compute_graph.add_node(src_idx)
            self.compute_graph.add_node(dst_idx)

            self.idx_to_node_set[src_idx] = edge.src
            self.idx_to_node_set[dst_idx] = edge.dst

            srcs.append(src_idx)
            dsts.append(dst_idx)

            self.compute_graph.add_edge(src_idx, dst_idx, weight=edge.oe.duration)

            # The output node set has a nonempty strict subset of active nodes
            active_node_subset = set(edge.dst.nodes).intersection(self.active_nodes)
            if active_node_subset and active_node_subset != set(edge.dst.nodes):
                dst_active_subset_idx = self.get_new_idx()
                self.compute_graph.add_node(dst_active_subset_idx)
                self.idx_to_node_set[dst_active_subset_idx] = NodeSet(list(active_node_subset))
                dsts.append(dst_active_subset_idx)
                self.compute_graph.add_edge(dst_idx, dst_active_subset_idx, weight=0)

        # Augment compute graph with edges between overlapping destination and source sets
        for dst in dsts:
            for src in srcs:
                if set(self.idx_to_node_set[dst].nodes).intersection(
                        set(self.idx_to_node_set[src].nodes)):
                    self.compute_graph.add_edge(dst, src, weight=0)

        # Find active node sets consisting entirely of active nodes
        for idx in self.compute_graph.nodes():
            if set(self.idx_to_node_set[idx].nodes).issubset(self.active_nodes) \
                    and len(set(self.idx_to_node_set[idx].nodes)) > 0:
                self.active_node_sets.add(idx)

        # Find edges required to recompute each node set given all active node sets are migrated
        for idx in self.compute_graph.nodes():
            recompute_edges = set()
            self.dfs(idx, set(), recompute_edges)
            self.recomputation_edges[idx] = recompute_edges

    # Compute the total cost to migrate the unique nodes specified node sets.
    def compute_migration_cost(self, node_sets):
        migrate_nodes = set().union(*[self.idx_to_node_set[i].nodes for i in node_sets])
        return sum([i.size for i in migrate_nodes]) / self.migration_speed_bps

    # Compute the total cost to recompute the specified node sets.
    def compute_recomputation_cost(self, node_sets):
        recompute_edges = set().union(*[self.recomputation_edges[i]
                                        for i in node_sets])
        return sum([self.compute_graph.get_edge_data(*i)["weight"]
                    for i in recompute_edges])

    # Compute the total cost to migrate the specified node sets.
    def total_cost(self, migrated_node_sets):
        return self.compute_migration_cost(migrated_node_sets) + \
               self.compute_recomputation_cost(
                   self.active_node_sets.difference(migrated_node_sets))

    def select_nodes(self):
        self.construct_graph()

        # start with migrating all, greedily un-migrate node sets
        migrated_node_sets = set()
        for node_set in self.active_node_sets:
            migrated_node_sets.add(node_set)

        while True:
            best_decrease = -np.inf
            best_set = None
            current_score = self.total_cost(migrated_node_sets)
            for node_set in migrated_node_sets:
                decrease = current_score - self.total_cost(
                    migrated_node_sets.difference({node_set}))
                if decrease > best_decrease:
                    best_decrease = decrease
                    best_set = node_set

            if best_decrease < 0:
                break
            migrated_node_sets = migrated_node_sets.difference({best_set})

        print("greedy migration cost:", self.total_cost(migrated_node_sets))

        migrated_nodes = set()
        for i in list(migrated_node_sets):
            for node in self.idx_to_node_set[i].nodes:
                migrated_nodes.add(node)
        return migrated_nodes
