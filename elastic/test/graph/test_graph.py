#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from unittest import mock
import uuid
from core.event import OperationEvent
from core.graph.graph import DependencyGraph
from core.graph.node import Node
from core.graph.node_set import NodeSet, NodeSetType
from core.graph.versioned_var import VersionedVariable


class TestDependencyGraph(unittest.TestCase):
    def test_add_edge(self):
        graph = DependencyGraph()
        
        src_nodes, dst_nodes = self.get_test_nodes(2), self.get_test_nodes(3)
        src, dst, oe = \
            NodeSet(src_nodes, NodeSetType.INPUT), NodeSet(dst_nodes, NodeSetType.OUTPUT), mock.MagicMock()
        graph.add_edge(src, dst, oe)
        
        self.assertEqual(1, len(graph.edges))
        self.assertEqual(graph.edges[0], src.edge)
        self.assertEqual(graph.edges[0], dst.edge)
        self.assertEqual(graph.edges[0].src, src)
        self.assertEqual(graph.edges[0].dst, dst)
        
    def test_add_active_node(self):
        graph = DependencyGraph()
        
        v1 = "oldVar"
        old_vid = id(v1)
        
        graph.add_active_node(self.get_named_test_node("v1", old_vid))
        self.assertEqual(1, len(graph.active_nodes))
        self.assertEqual(old_vid, graph.active_nodes["v1"].var.vid)
        
        v1 = "newVar"
        new_vid = id(v1)
        self.assertNotEqual(old_vid, new_vid)
        
        graph.add_active_node(self.get_named_test_node("v1", new_vid))
        self.assertEqual(1, len(graph.active_nodes))
        self.assertEqual(new_vid, graph.active_nodes["v1"].var.vid)

    def get_test_node(self):
        var = uuid.uuid4()
        return Node(VersionedVariable(var.hex, id(var), 1))
    
    def get_named_test_node(self, name, vid, ver=1):
        return Node(VersionedVariable(name, vid, ver))

    def get_test_nodes(self, count):
        return [self.get_test_node() for _ in range(count)]


if __name__ == '__main__':
    unittest.main()
