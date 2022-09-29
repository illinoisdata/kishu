#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.notebook.operation_event import OperationEvent
from core.graph.node_set import NodeSet

# An edge in the dependency graph corresponds to an operation event.
class Edge:
    def __init__(self, oe: OperationEvent, src: NodeSet, dst: NodeSet) -> None:
        self.oe = oe

        # Source/input node set of the operation event.
        self.src = src

        # Destination/output node set of the operation event.
        self.dst = dst
