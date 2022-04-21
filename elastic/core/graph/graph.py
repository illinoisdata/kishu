#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import logging
from core.event import OperationEvent
from core.graph.edge import Edge
from core.graph.node import Node
from core.graph.node_set import NodeSet, NodeSetType

logger = logging.getLogger(__name__)

class DependencyGraph:
    def __init__(self) -> None:
        self.edges = []
        self.active_nodes = {}
        self.sink = NodeSet(nodes=[], type=NodeSetType.DUMMY)
        
    def add_edge(self, src: NodeSet, dst: NodeSet, oe: OperationEvent):
        edge = Edge(oe, src, dst)
        self.edges.append(edge)
        src.edge = edge
        dst.edge = edge
        
    def add_active_node(self, node: Node):
        if node.var.name in self.active_nodes:
            # FIXME: when an active node is overwritten, detach the underlying variable to enable garbage collection
            #   Note: It's also possible that a new version of the same variable is created.
            logger.warn("Variable {} may have been overwritten.".format(node.var.name))
        self.active_nodes[node.var.name] = node
