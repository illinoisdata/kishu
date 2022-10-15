#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois


# A variable snapshot in the dependency graph corresponds to a version of a variable.
# I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have
# 3 corresponding variable snapshots.
class VariableSnapshot:
    def __init__(self, name, version, index) -> None:
        # Pointers for graph reconstruction
        self.name = name
        self.version = version

        # This VS is the 'index'th VS to be defined in its OE. Required for correct order of redefinition.
        self.index = index

        # Whether this VS corresponds to a deleted variable.
        # i.e. if this VS was created for 'del x' we set this to true so this variable is explicitly not considered
        # for migration.
        self.deleted = False

        # Output nodeset in the dependency graph containing this variable snapshot.
        self.output_nodeset = None

        # Input nodesets in the dependency graph containing this variable snapshot.
        self.input_nodesets = []

        # Size of variable pointed to by VS; estimated at migration time.
        self.size = 0


