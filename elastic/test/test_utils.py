#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.operation_event import OperationEvent
from elastic.core.graph.node_set import NodeSet, NodeSetType


def get_test_input_nodeset(vss: list):
    return NodeSet(vss, NodeSetType.INPUT)


def get_test_output_nodeset(vss: list):
    return NodeSet(vss, NodeSetType.OUTPUT)


def get_test_dummy_nodeset(vss: list):
    return NodeSet(vss, NodeSetType.DUMMY)


def get_test_vs(name: str, ver=1, index=0, deleted=False):
    """
        Fast variable snapshot creation with pre-filled fields.
    """
    return VariableSnapshot(name, ver, index, deleted)


def get_test_oe(cell_num: int, cell="", cell_runtime=1, start_time=1,
                src=NodeSet([], NodeSetType.INPUT), dst=NodeSet([], NodeSetType.OUTPUT)):
    """
        Fast operation event creation with pre-filled fields.
    """
    return OperationEvent(cell_num, cell, cell_runtime, start_time, src, dst)


def get_problem_setting():
    """
        Returns the graph containing the test problem setting for the optimizers.
        (cost:2) "x"  "y" (cost: 2)
             c3   |    |  c2
                 "z" "z"
                   "z"
                    | c1 (cost: 3)
                   []
    """
    graph = DependencyGraph()

    # Variable snapshots
    vs1 = graph.create_variable_snapshot("x", 0, False)
    vs2 = graph.create_variable_snapshot("y", 0, False)
    vs3 = graph.create_variable_snapshot("z", 0, True)
    vs1.size = 2
    vs2.size = 2
    active_vss = [vs1, vs2]

    # Nodesets
    src1 = NodeSet([], NodeSetType.INPUT)
    dst1 = NodeSet([vs3], NodeSetType.OUTPUT)
    src2 = NodeSet([vs3], NodeSetType.INPUT)
    dst2 = NodeSet([vs1], NodeSetType.OUTPUT)
    src3 = NodeSet([vs3], NodeSetType.INPUT)
    dst3 = NodeSet([vs2], NodeSetType.OUTPUT)

    # Operation events
    graph.add_operation_event("", 3, 0, src1, dst1)
    graph.add_operation_event("", 0.1, 0, src2, dst2)
    graph.add_operation_event("", 0.1, 0, src3, dst3)

    return graph, active_vss
