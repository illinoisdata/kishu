#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from enum import Enum
from typing import List
from elastic.core.graph.variable_snapshot import VariableSnapshot


class NodeSetType(Enum):
    """
        Type of the node set is whether the node set is an input or output of an operation event.
    """

    # The nodeset is the input nodeset of an OE.
    INPUT = 1

    # The nodeset is the output nodeset of an OE.
    OUTPUT = 2

    # The nodeset is temporarily constructed during graph augmentation stage of an optimization algorithm.
    DUMMY = 3


class NodeSet:
    """
        A node set is the set of input/output variable snapshots of an operation event.
    """
    def __init__(self, vs_list: List[VariableSnapshot], nodeset_type: NodeSetType):
        """
            Initialize a noteset from a list of variable snapshots.
            Args:
                vs_list (list): list of variable snapshots.
                nodeset_type (NodeSetType): type of nodeset.
        """

        self.vs_list = vs_list

        # Accordingly set this node set as the input/output node set of its variable snapshots.
        for vs in self.vs_list:
            if nodeset_type == NodeSetType.OUTPUT:
                vs.output_nodeset = self
            elif nodeset_type == NodeSetType.INPUT:
                vs.input_nodesets.append(self)
        self.type = nodeset_type

        # The operation event this node set is adjacent to.
        self.operation_event = None
