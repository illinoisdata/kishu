#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import logging
from collections import defaultdict

from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.operation_event import OperationEvent
from elastic.core.graph.node_set import NodeSet


class DependencyGraph:
    """
        A dependency graph is a snapshot of the history of a notebook instance.
        Nodesets and operation events are the nodes and edges of the dependency graph.
    """
    def __init__(self):
        """
            Create a new dependency graph. Called when the magic extension of elastic notebook is loaded with %load_ext.
        """
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

    def create_variable_snapshot(self, variable_name: str, index: int, deleted: bool) -> VariableSnapshot:
        """
            Creates a new variable snapshot for a given variable.
            Args:
                variable_name (str): variable_name
                index (int): This VS is the 'index'th VS to be defined in its OE. Required for correct order of
                    redefinition post-migration.
                deleted (bool): Whether this VS is created for the deletion of a variable, i.e. 'del x'.
        """

        # Assign a version number to the VS.
        if variable_name in self.variable_snapshots:
            version = len(self.variable_snapshots[variable_name])
        else:
            version = 0

        # Create a new VS instance and store it in the graph.
        vs = VariableSnapshot(variable_name, version, index, deleted)
        self.variable_snapshots[variable_name].append(vs)

        return vs

    def add_operation_event(self, cell, cell_runtime: float, start_time: float, src: NodeSet, dst: NodeSet):
        """
            Create an operation event from cell execution metrics.
            Args:
                cell (str): Raw cell cell.
                cell_runtime (float): Cell runtime.
                start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                    queued.
                src (Nodeset): Nodeset containing input VSs of the cell execution.
                dst(NodeSet): Nodeset containing output VSs of the cell execution.
        """

        # Create an operation event.
        oe = OperationEvent(len(self.operation_events), cell, cell_runtime, start_time, src, dst)

        # Add the newly created OE to the graph.
        self.operation_events.append(oe)

        # Set the newly added OE as the adjacent OE of its input and output nodesets.
        src.operation_event = oe
        dst.operation_event = oe

        # Add the input and output nodesets to the graph.
        self.input_nodesets.append(src)
        self.output_nodesets.append(dst)
