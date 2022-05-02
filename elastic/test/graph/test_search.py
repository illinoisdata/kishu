#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from unittest import mock
from core.event import OperationEvent, operation_events

from core.graph.graph import DependencyGraph
from core.graph.node import Node
from core.graph.node_set import NodeSet, NodeSetType
from core.graph.search import find_path
from core.graph.versioned_var import VersionedVariable
import numpy as np


class TestFindPath(unittest.TestCase):
    def setUp(self):
        global operation_events
        operation_events = []
        
    def tearDown(self):
        global operation_events
        operation_events = []
    
    def test_find_path_empty_graph(self):
        graph, migrated_nodes = DependencyGraph(), []
        recompute_seq = find_path(graph, migrated_nodes, [])
        self.assertEqual(0, len(recompute_seq))
        
    def test_find_path_two_nodesets(self):
        graph = DependencyGraph()
        
        oe1v1 = np.array([])
        src_nodes, dst_nodes = [], [self.get_named_test_node("oe1v1", id(oe1v1))]
        src, dst, oe = \
            NodeSet(src_nodes, NodeSetType.INPUT), NodeSet(dst_nodes, NodeSetType.OUTPUT), mock.MagicMock()
        graph.add_edge(src, dst, oe)
        graph.add_active_nodes(dst_nodes)
        
        global operation_events
        operation_events.append(oe)
        oe.get_exec_id.return_value = 0
        
        recompute_seq = find_path(graph, dst_nodes, operation_events)
        self.assertEqual(0, len(recompute_seq))
        
        recompute_seq = find_path(graph, [], operation_events)
        self.assertEqual(1, len(recompute_seq))
    
    def test_find_path_multiple_edges(self):
        graph = DependencyGraph()
        
        oe1v1 = np.array([])
        src_nodes, dst_nodes = [], [self.get_named_test_node("oe1v1", id(oe1v1))]
        src, dst, oe1 = \
            NodeSet(src_nodes, NodeSetType.INPUT), NodeSet(dst_nodes, NodeSetType.OUTPUT), self.get_oe(0)
        graph.add_edge(src, dst, oe1)
        graph.add_active_nodes(dst_nodes)
        
        oe2v1, oe2v2 = np.ones(1), np.zeros(2)
        src_nodes, dst_nodes = dst_nodes, [self.get_named_test_node("oe2v1", id(oe2v1)),
                                           self.get_named_test_node("oe2v2", id(oe2v2))]
        src, dst, oe2 = \
            NodeSet(src_nodes, NodeSetType.INPUT), NodeSet(dst_nodes, NodeSetType.OUTPUT), self.get_oe(1)
            
        global operation_events
        operation_events += [oe1, oe2]
        
        graph.add_edge(src, dst, oe2)
        graph.add_active_nodes(dst_nodes)
        recompute_seq = find_path(graph, dst_nodes, operation_events)
        self.assertEqual(1, len(recompute_seq)) # 1 var in oe1 is still active
        
        recompute_seq = find_path(graph, [dst_nodes[0]], operation_events)
        self.assertEqual(2, len(recompute_seq)) # 1 var in oe1 and 1 var in oe2 need to be recomputed
        
    def get_named_test_node(self, name, vid, ver=1):
        return Node(VersionedVariable(name, vid, ver))
    
    def get_oe(self, exec_id):
        return OperationEvent(exec_id, None, None, None, "", "", [])