#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import datetime
import inspect
import uuid

from core.graph.graph import DependencyGraph
from core.graph.edge import Edge
from core.graph.node import Node
from core.graph.node_set import NodeSet, NodeSetType
from core.graph.versioned_var import VersionedVariable
from core.container import DataContainer, OperationContainer
from core.event import OperationEvent, data_events, data_containers, data_container_version, operation_events,\
    operation_event_lookup

def ConvertGraph():
    graph = DependencyGraph()

    # Add data containers nodes
    nodes = {}
    for data_container in data_containers:
        versioned_variable = VersionedVariable(data_container.get_name(), data_container.get_base_id(),
                                               data_container.get_version())
        node = Node(versioned_variable, data_container, data_container.get_size())

        # If node is of the latest version, it is an active node.
        if data_container.get_version() == data_container_version[data_container.get_name()]:
            graph.add_active_node(node)

        nodes[(data_container.get_name(), data_container.get_version())] = node

    # Add operation events as edges
    for operation_event in operation_events:
        # Find input nodes from related data events
        input_nodes = []
        unique_data_containers = set()
        for data_event in operation_event.related_data_events:
            data_container = data_event.container
            if data_container.get_name() not in unique_data_containers:
                input_nodes.append(nodes[(data_container.get_name(), data_container.get_version())])
                unique_data_containers.add(data_event.container.get_name())
        input_nodeset = NodeSet(input_nodes, NodeSetType.INPUT)
        input_nodeset.add_input_nodeset()

        # Find output nodes from output data containers
        output_nodes = []
        for data_container in operation_event.output_data_containers:
            output_nodes.append(nodes[(data_container.get_name(), data_container.get_version())])
        output_nodeset = NodeSet(output_nodes, NodeSetType.OUTPUT)
        output_nodeset.set_output_nodeset()

        # Create edge
        graph.add_edge(input_nodeset, output_nodeset, operation_event)

    return graph
