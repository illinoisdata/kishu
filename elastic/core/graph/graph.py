#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import logging
import types
from elastic.core.notebook.operation_event import OperationEvent
from elastic.core.notebook.variable_snapshot import VariableSnapshot, VariableSnapshotSet
from elastic.core.notebook.record_event import RecordEvent
from elastic.core.graph.edge import Edge
from elastic.core.graph.node_set import NodeSet
from elastic.core.graph.recompute import find_edges_to_recompute
import elastic.core.globals

logger = logging.getLogger(__name__)


# A dependency graph is a snapshot of the history of a notebook instance.
class DependencyGraph:
    def __init__(self) -> None:
        # Edges of the dependency graph representing the cell executions (operation events).
        self.edges = []

        # Active nodes are nodes corresponding to the latest instances/versions of each variable (variable snapshots).
        self.active_nodes = []

        # Subset of active nodes requiring recomputation post-migration (due to being trimmed pre-migration).
        self.nodes_to_recompute = []

    def add_edge(self, src: NodeSet, dst: NodeSet, oe: OperationEvent):
        edge = Edge(oe, src, dst)
        self.edges.append(edge)
        src.edge = edge
        dst.edge = edge

    # Reduce the size of the graph for migration by deleting the contents of some nodes (and recomputing them post-
    # migration).

    def trim_graph(self, selector):
        selector.dependency_graph = self
        selector.active_nodes = self.active_nodes
        nodes_to_migrate = selector.select_nodes()

        print("---------------------------")
        print("Nodes to migrate:")
        for node in nodes_to_migrate:
            print(node.vs.get_name(), node.vs.get_version(), node.vs.get_size())

        self.nodes_to_recompute = set(self.active_nodes) - set(nodes_to_migrate)

        # Delete the contents of the nodes to recompute
        for node in self.nodes_to_recompute:
            node.vs.clear_item()

    # Recompute non-migrated nodes post-migration by re-executing some cells.
    def recompute_graph(self):
        globals_dict = dict(**globals())
        # Reconstruct operation events and variable snapshots
        snapshot_dict = {}
        libraries_edge = None
        for edge in self.edges:
            elastic.core.globals.operation_events.append(edge.oe)
            for node in edge.src.nodes + edge.dst.nodes:
                if (node.name, node.version) not in snapshot_dict:
                    node.vs = VariableSnapshot(node.name, node.version, node.vs, node.prev_oe)
                    elastic.core.globals.variable_snapshots.append(node.vs)
                    snapshot_dict[(node.name, node.version)] = node.vs
                else:
                    node.vs = snapshot_dict[(node.name, node.version)]

            edge.oe.input_variable_snapshots.clear()
            edge.oe.output_variable_snapshots.clear()
            for node in edge.src.nodes:
                edge.oe.input_variable_snapshots.append(node.vs)
            for node in edge.dst.nodes:
                edge.oe.output_variable_snapshots.append(node.vs)
            
            if edge.oe.cell_func_name == "import_libraries":
                libraries_edge = edge

        # Recompute edges
        edges_to_recompute = find_edges_to_recompute(self)
        edges_to_recompute.sort(key=lambda x: x.oe.start)
        if libraries_edge:
            edges_to_recompute.insert(0, libraries_edge)
        for edge in edges_to_recompute:
            print("Recomputing edge " + edge.oe.cell_func_name + "...")

            # declare input nodes into the kernel
            for node in edge.src.nodes:
                globals_dict[node.vs.get_name()] = node.vs.get_item()

            # Run cell code
            func = types.FunctionType(edge.oe.cell_func_code, globals_dict, edge.oe.cell_func_name)
            output_variable_snapshot_set = func().variable_snapshots
            print(output_variable_snapshot_set)

            # Assign outputs to output nodes
            for node in edge.dst.nodes:
                node.vs.set_item(output_variable_snapshot_set[node.vs.get_name()])
                # update globals() if output nodes are libraries
                if edge.oe.cell_func_name == "import_libraries":
                    globals_dict[node.vs.get_name()] = node.vs.get_item()

        # Clear old versions of variables
        for edge in edges_to_recompute:
            for node in edge.dst.nodes:
                if node.version < elastic.core.globals.variable_version[node.name]:
                    node.vs.clear_item()

        self.nodes_to_recompute.clear()

    # Declares active nodes and functions into the kernel.
    def reconstruct_notebook(self):
        for node in self.active_nodes:
            globals()[node.vs.get_name()] = node.vs
            exec("global {}".format(node.vs.get_name()))
            exec("{} = node.vs".format(node.vs.get_name()))

        for edge in self.edges:
            globals()[edge.oe.cell_func_name] = edge.oe.cell_func_code
            exec("global {}".format(edge.oe.cell_func_name))
            exec("{} = edge.oe.cell_func_code".format(edge.oe.cell_func_name))
        print(locals().keys())
        print(globals().keys())
