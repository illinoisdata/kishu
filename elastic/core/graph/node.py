#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.graph.versioned_var import VersionedVariable
from core.container import DataContainer


class Node:
    def __init__(self, var: VersionedVariable, dc: DataContainer, size, output_nodeset=None) -> None:
        self.var = var
        self.dc = dc
        self.size = size
        self.output_nodeset = output_nodeset
        self.input_nodesets = []

    def add_input_nodeset(self, nodeSet):
        self.input_nodesets.append(nodeSet)
        
    def get_size(self):
        return self.size
