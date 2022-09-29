#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from enum import Enum
from typing import List
from core.graph.node import Node

# Type of the node set is whether the node set is an input or output of an edge.
class NodeSetType(Enum):
    INPUT = 1
    OUTPUT = 2
    DUMMY = 3
    
# A node set is the set of input/output nodes of an edge.
class NodeSet:
    def __init__(self, nodes: List[Node], type: NodeSetType) -> None:
        self.nodes = nodes

        # Accordingly set this node set as the input/output node set of its nodes
        for node in self.nodes:
            if type == NodeSetType.OUTPUT:
                node.output_nodeset = self
            elif type == NodeSetType.INPUT:
                node.input_nodesets.append(self)
        self.type = type

        # The edge this node set is adjacent to.
        self.edge = None
