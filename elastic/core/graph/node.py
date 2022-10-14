#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.notebook.variable_snapshot import VariableSnapshot

# A node in the dependency graph corresponds to a variable snapshot.
class Node:
    def __init__(self, vs: VariableSnapshot) -> None:
        self.vs = vs

        # Output nodeset in the dependency graph containing this node.
        self.output_nodeset = None

        # Input nodesets in the dependency graph containing this node.
        self.input_nodesets = []

        # Pointers for graph reconstruction
        self.name = vs.get_name()
        self.version = vs.get_version()
        self.prev_oe = vs.get_prev_oe()
        self.size = vs.get_size()
