#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.graph.node_set import NodeSet
from core.graph.versioned_var import VersionedVariable


class Node:
    def __init__(self, var: VersionedVariable, output_nodeset: NodeSet) -> None:
        self.var = var
        self.output_nodeset = output_nodeset
        self.input_nodesets = []

    def add_nodeset(self, nodeSet: NodeSet):
        self.input_nodesets.append(nodeSet)
