#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import datetime
import inspect
import uuid

from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.node import Node
from elastic.core.graph.node_set import NodeSet, NodeSetType
from elastic.core.globals import variable_snapshots, operation_events, variable_version


def create_graph():
    graph = DependencyGraph()

    # Create a node for each variable snapshot and add to graph
    nodes = {}
    for variable_snapshot in variable_snapshots:
        node = Node(variable_snapshot)

        # If node is of the latest version of a variable, it is an active node.
        if variable_snapshot.get_version() == variable_version[variable_snapshot.get_name()]:
            graph.active_nodes.append(node)

        if not variable_snapshot.get_migrate_flag():
            node.vs.clear_item()

        nodes[(variable_snapshot.get_name(), variable_snapshot.get_version())] = node

    # Create an edge for each operation event and add to graph
    for operation_event in operation_events:
        # Create input node set
        input_nodes = [nodes[(variable_snapshot.get_name(), variable_snapshot.get_version())]
                        for variable_snapshot in operation_event.input_variable_snapshots]
        input_nodeset = NodeSet(input_nodes, NodeSetType.INPUT)

        # Create output node set
        output_nodes = [nodes[(variable_snapshot.get_name(), variable_snapshot.get_version())]
                        for variable_snapshot in operation_event.output_variable_snapshots]
        output_nodeset = NodeSet(output_nodes, NodeSetType.OUTPUT)

        if not variable_snapshot.get_migrate_flag():
            operation_event.output_variable_snapshots.clear()

        graph.add_edge(input_nodeset, output_nodeset, operation_event)

    return graph
