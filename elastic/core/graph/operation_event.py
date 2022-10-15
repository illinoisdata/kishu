#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from elastic.core.graph.node_set import NodeSet


# An edge in the dependency graph corresponds to an operation event.
class OperationEvent:
    def __init__(self, cell_num, code, duration: float, start_time: float, src: NodeSet, dst: NodeSet) -> None:
        self.cell_num = cell_num
        self.code = code
        self.duration = duration
        self.start_time = start_time

        # Source/input node set of the operation event.
        self.src = src

        # Destination/output node set of the operation event.
        self.dst = dst
