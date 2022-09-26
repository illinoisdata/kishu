#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from unittest import mock
import uuid
from core.graph.graph import DependencyGraph
from core.graph.node import Node
from core.graph.node_set import NodeSet, NodeSetType
from core.notebook.variable_snapshot import VariableSnapshot

VAR_SIZE=1024


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

    def get_test_node(self, name, ver=1):
        return Node(VariableSnapshot(name, ver, None, None))

    def get_test_nodes(self, count):
        return [self.get_test_node(str(i), 1) for i in range(count)]


if __name__ == '__main__':
    unittest.main()
