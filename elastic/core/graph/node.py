#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.graph.versioned_var import VersionedVariable


class Node:
    def __init__(self, var: VersionedVariable, output_nodeset=None) -> None:
        self.var = var
        self.output_nodeset = output_nodeset
        self.input_nodesets = []

    def add_nodeset(self, nodeSet):
        self.input_nodesets.append(nodeSet)
