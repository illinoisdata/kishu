#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from elastic.algorithm.selector import Selector
from elastic.core.graph.node_set import NodeSet
import networkx as nx
import numpy as np
import math


class OptimizerExact(Selector):
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

        # Cost of migrating nothing. Used for normalization in submodular optimization.
        self.migrate_none_cost = 0

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
        self.compute_graph = nx.DiGraph()
        self.active_nodes = set(self.active_nodes)
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
        
    def select_nodes(self):
        self.construct_graph()

        # Construct graph for computing mincut
        mincut_graph = nx.DiGraph()

        all_active_nodes = set().union(*[self.idx_to_node_set[i].nodes for i in self.active_node_sets])
        all_operations = set().union(*[self.recomputation_edges[i] for i in self.active_node_sets])

        mincut_graph.add_node("source")
        mincut_graph.add_node("sink")

        for active_node in all_active_nodes:
            mincut_graph.add_node(active_node)
            mincut_graph.add_edge("source", active_node, capacity=active_node.vs.get_size() / self.migration_speed_bps)

        for operation in all_operations:
            mincut_graph.add_node(operation)
            mincut_graph.add_edge(operation, "sink", capacity=self.compute_graph.get_edge_data(*operation)["weight"])

        for idx in self.active_node_sets:
            mincut_graph.add_node(idx)
            for active_node in self.idx_to_node_set[idx].nodes:
                mincut_graph.add_edge(active_node, idx, capacity=np.inf)
            for operation in self.recomputation_edges[idx]:
                mincut_graph.add_edge(idx, operation, capacity=np.inf)

        cut_value, partition = nx.minimum_cut(mincut_graph, "source", "sink")
        print("minimum migration cost:", cut_value)
        migrated_node_sets = set(partition[1]).intersection(self.active_node_sets)

        migrated_nodes = set()
        for i in list(migrated_node_sets):
            for node in self.idx_to_node_set[i].nodes:
                migrated_nodes.add(node)
        return migrated_nodes
