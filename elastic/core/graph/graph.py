#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import logging
from collections import defaultdict

from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.operation_event import OperationEvent
from elastic.core.graph.node_set import NodeSet

logger = logging.getLogger(__name__)


# A dependency graph is a snapshot of the history of a notebook instance.
class DependencyGraph:
    def __init__(self) -> None:
        # Operation events represent the cell executions and form the edges of the graph.
        self.operation_events = []

        # Dict of variable snapshots (versioned variables).
        # Keys are variable names, while values are lists of the actual VSs.
        # i.e. {"x": [(x, 1), (x, 2)], "y": [(y, 1), (y, 2), (y, 3)]}
        self.variable_snapshots = defaultdict(list)

        # Input nodesets are the input VSs to OEs.
        self.input_nodesets = []

        # Input nodesets are the input VSs to OEs.
        self.output_nodesets = []

    # Creates a new variable snapshot for a given variable.
    def create_variable_snapshot(self, variable_name, index) -> VariableSnapshot:
        # Edge case
        if variable_name in self.variable_snapshots:
            version = len(self.variable_snapshots[variable_name])
        else:
            version = 0
        vs = VariableSnapshot(variable_name, version, index)
        self.variable_snapshots[variable_name].append(vs)
        return vs

    def add_operation_event(self, code, duration: float, start_time: float, src: NodeSet, dst: NodeSet):
        # Create an operation event
        oe = OperationEvent(len(self.operation_events), code, duration, start_time, src, dst)
        self.operation_events.append(oe)

        src.operation_event = oe
        dst.operation_event = oe
        self.input_nodesets.append(src)
        self.output_nodesets.append(dst)
