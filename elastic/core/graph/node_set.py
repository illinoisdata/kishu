#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from enum import Enum
from typing import List
from elastic.core.graph.variable_snapshot import VariableSnapshot


# Type of the node set is whether the node set is an input or output of an operation event.
class NodeSetType(Enum):
    INPUT = 1
    OUTPUT = 2
    DUMMY = 3


# A node set is the set of input/output variable snapshots of an operation event.
class NodeSet:
    def __init__(self, vs_list: List[VariableSnapshot], nodeset_type: NodeSetType) -> None:
        self.vs_list = vs_list

        # Accordingly set this node set as the input/output node set of its variable snapshots
        for vs in self.vs_list:
            if nodeset_type == NodeSetType.OUTPUT:
                vs.output_nodeset = self
            elif nodeset_type == NodeSetType.INPUT:
                vs.input_nodesets.append(self)
        self.type = nodeset_type

        # The operation event this node set is adjacent to.
        self.operation_event = None
