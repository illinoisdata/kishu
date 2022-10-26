#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from elastic.core.graph.node_set import NodeSet, NodeSetType
from elastic.test.test_utils import get_test_vs


class TestNodeset(unittest.TestCase):

    def test_input_nodeset(self):
        """
            Test creating an input nodeset from VSs correctly appends the nodeset to the input nodeset field in the VS.
        """
        vs = get_test_vs("x")

        nodeset1 = NodeSet([vs], nodeset_type=NodeSetType.INPUT)
        self.assertTrue(vs.input_nodesets[0] == nodeset1)

        nodeset2 = NodeSet([vs], nodeset_type=NodeSetType.INPUT)
        self.assertTrue(vs.input_nodesets[1] == nodeset2)

    def test_output_nodeset(self):
        """
            Test creating an input nodeset from VSs correctly sets the nodeset as the output nodeset of the VS.
        """
        vs = get_test_vs("x")

        nodeset1 = NodeSet([vs], nodeset_type=NodeSetType.OUTPUT)
        self.assertTrue(vs.output_nodeset == nodeset1)

    def test_dummy_nodeset(self):
        """
            Test creating a dummy nodeset from VSs does not overwrite its input or output nodesets.
        """
        vs = get_test_vs("x")

        src = NodeSet([vs], nodeset_type=NodeSetType.INPUT)
        src2 = NodeSet([vs], nodeset_type=NodeSetType.INPUT)
        dst = NodeSet([vs], nodeset_type=NodeSetType.OUTPUT)
        dummy = NodeSet([vs], nodeset_type=NodeSetType.DUMMY)

        self.assertEqual(2, len(vs.input_nodesets))
        self.assertTrue(vs.input_nodesets[0] == src)
        self.assertTrue(vs.input_nodesets[1] == src2)
        self.assertTrue(vs.output_nodeset == dst)


if __name__ == '__main__':
    unittest.main()
