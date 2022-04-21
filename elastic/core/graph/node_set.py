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
        self.type = type
