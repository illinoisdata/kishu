#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from enum import Enum
from typing import List
from core.graph.node import Node

class NodeSetType(Enum):
    INPUT = 1
    OUTPUT = 2
    DUMMY = 3
    

class NodeSet:
    def __init__(self, nodes: List[Node], type: NodeSetType) -> None:
        self.nodes = nodes
        if type == NodeSetType.OUTPUT:
            self.set_output_nodeset()
        self.type = type
        self.edge = None
    
    def set_edge(self, edge):
        if self.edge is not None:
            raise Exception("NodeSet {} is already connected by an edge".format(self))
        self.edge = edge
        
    def set_output_nodeset(self):
        for node in self.nodes:
            node.output_nodeset = self

    def add_input_nodeset(self):
        for node in self.nodes:
            node.input_nodesets.append(self)
