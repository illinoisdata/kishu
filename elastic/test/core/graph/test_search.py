#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from unittest import mock
from elastic.core.notebook.operation_event import OperationEvent

from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.node_set import NodeSet, NodeSetType
from elastic.core.graph.find_oes_to_recompute import find_edges_to_recompute
from elastic.core.notebook.variable_snapshot import VariableSnapshot
import numpy as np

VAR_SIZE=1024

class TestFindPath(unittest.TestCase):
    def setUp(self):
        global operation_events
        operation_events = []
        
    def tearDown(self):
        global operation_events
        operation_events = []
    
    def test_find_path_empty_graph(self):
        graph = DependencyGraph()
        recompute_seq = find_edges_to_recompute(graph)
        self.assertEqual(0, len(recompute_seq))
        
    def test_find_path_two_nodesets(self):
        graph = DependencyGraph()

        src_nodes, dst_nodes = [], [self.get_test_node("oe1v1", 1)]
        src, dst, oe = \
            NodeSet(src_nodes, NodeSetType.INPUT), NodeSet(dst_nodes, NodeSetType.OUTPUT), mock.MagicMock()
        graph.add_operation_event(src, dst, oe)
        graph.nodes_to_recompute = dst_nodes

        recompute_seq = find_edges_to_recompute(graph)
        self.assertEqual(1, len(recompute_seq))
    
    def test_find_path_multiple_edges(self):
        graph = DependencyGraph()
        
        oe1v1 = np.array([])
        src_nodes, dst_nodes = [], [self.get_test_node("oe1v1", 1)]
        src, dst, oe1 = \
            NodeSet(src_nodes, NodeSetType.INPUT), NodeSet(dst_nodes, NodeSetType.OUTPUT), self.get_oe(0)
        graph.add_operation_event(src, dst, oe1)
        graph.nodes_to_recompute = dst_nodes

        src_nodes, dst_nodes = dst_nodes, [self.get_test_node("oe2v1", 1),
                                           self.get_test_node("oe2v2", 2)]
        src, dst, oe2 = \
            NodeSet(src_nodes, NodeSetType.INPUT), NodeSet(dst_nodes, NodeSetType.OUTPUT), self.get_oe(1)
        graph.add_operation_event(src, dst, oe2)

        graph.nodes_to_recompute = src_nodes
        recompute_seq = find_edges_to_recompute(graph)
        self.assertEqual(1, len(recompute_seq)) # 1 var in oe1 is still active

        graph.nodes_to_recompute = src_nodes + [dst_nodes[0]]
        recompute_seq = find_edges_to_recompute(graph)
        self.assertEqual(2, len(recompute_seq)) # 1 var in oe1 and 1 var in oe2 need to be recomputed

    def get_test_node(self, name, ver=1):
        return VariableSnapshot(VariableSnapshot(name, ver, None, None))
    
    def get_oe(self, exec_id):
        return OperationEvent(exec_id, None, None, None, "", "", [])
