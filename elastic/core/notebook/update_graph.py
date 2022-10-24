#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import dis

from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.node_set import NodeSet, NodeSetType


# Updates the graph according to the newly executed cell code.
def update_graph(cell, cell_runtime, start_time, graph: DependencyGraph):
    # Disassemble cell instructions
    instructions = dis.get_instructions(cell)

    # Capture input and output variables
    input_variables = {}
    output_variables = {}

    index = 0
    for instruction in instructions:
        """
        TODO: Handle one remaining edge case. See examples/numpy.ipynb:
            np.set_seed(0)
        For simplicity, we assume all class methods (i.e. list.sort()) will modify the class instance when called.
        In this case, 'np' should be both an input and output variable of the cell.
        The code below currently only identifies np as an input variable of the cell.
        """
        # Input variable
        if instruction.opname == "LOAD_NAME" and (instruction.argrepr not in input_variables) and \
                (instruction.argrepr not in output_variables):
            # Handles the case where argrepr is a builtin (i.e. 'len()').
            if instruction.argrepr in graph.variable_snapshots:
                input_variables[instruction.argrepr] = graph.variable_snapshots[instruction.argrepr][-1]

        # Output variable
        elif instruction.opname == "STORE_NAME" or instruction.opname == "DELETE_NAME":
            if instruction.argrepr not in output_variables:
                output_variables[instruction.argrepr] = graph.create_variable_snapshot(instruction.argrepr, index)
                index += 1
            if instruction.opname == "STORE_NAME":
                output_variables[instruction.argrepr].deleted = False
            else:
                output_variables[instruction.argrepr].deleted = True

    # Create nodesets for input and output variables
    input_nodeset = NodeSet(list(input_variables.values()), NodeSetType.INPUT)
    output_nodeset = NodeSet(list(output_variables.values()), NodeSetType.OUTPUT)

    # Add the newly created OE to the graph.
    graph.add_operation_event(cell, cell_runtime, start_time, input_nodeset, output_nodeset)
