#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import dis

from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.node_set import NodeSet, NodeSetType


def update_graph(cell: str, cell_runtime: float, start_time: float, input_variables: set, output_variables: dict,
                 graph: DependencyGraph):
    """
        Updates the graph according to the newly executed cell and its input and output variables.
        Args:
             cell (str): Raw cell cell.
             cell_runtime (float): Cell runtime.
             start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                 queued.
             input_variables (set): Set of input variables of the cell.
             output_variables (Dict): Dict of output variables. Keys are variables and values are 2-item lists
                 representing (order the variables were accessed / created in this cell,
                 variable is deleted at end of cell execution.)
             graph (DependencyGraph): Dependency graph representation of the notebook.
    """

    # Retrieve input variable snapshots
    input_vss = [graph.variable_snapshots[variable][-1] for variable in input_variables]

    # Create output variable snapshots
    output_vss = [graph.create_variable_snapshot(k, v[0], v[1]) for k, v in output_variables.items()]

    # Create nodesets for input and output variables snapshots
    input_nodeset = NodeSet(input_vss, NodeSetType.INPUT)
    output_nodeset = NodeSet(output_vss, NodeSetType.OUTPUT)

    # Add the newly created OE to the graph.
    graph.add_operation_event(cell, cell_runtime, start_time, input_nodeset, output_nodeset)
