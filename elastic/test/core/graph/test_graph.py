#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from elastic.core.graph.graph import DependencyGraph
from elastic.test.test_utils import get_test_input_nodeset, get_test_output_nodeset


class TestGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph()

    def test_create_variable_snapshot(self):
        """
            Test graph correctly handles versioning of VSs with the same and different names.
        """
        vs1 = self.graph.create_variable_snapshot("x", 1, False)
        vs2 = self.graph.create_variable_snapshot("x", 1, False)
        vs3 = self.graph.create_variable_snapshot("y", 1, False)

        # VSs are versioned correcly
        self.assertEqual(0, vs1.version)
        self.assertEqual(1, vs2.version)  # vs2 is second VS for variable x
        self.assertEqual(0, vs3.version)

        # VSs are stored in the graph correctly
        self.assertEqual({"x", "y"}, set(self.graph.variable_snapshots.keys()))
        self.assertEqual(2, len(self.graph.variable_snapshots["x"]))
        self.assertEqual(1, len(self.graph.variable_snapshots["y"]))

    def test_add_operation_event(self):
        src = get_test_input_nodeset([])
        dst = get_test_output_nodeset([])
        self.graph.add_operation_event("", 1, 1, src, dst)

        # OE and nodesets are stored in the graph correctly
        self.assertEqual(1, len(self.graph.operation_events))
        self.assertEqual(1, len(self.graph.input_nodesets))
        self.assertEqual(1, len(self.graph.output_nodesets))

        # Newly create OE correctly set as adjacent OE of input and output nodesets
        self.assertTrue(src.operation_event == self.graph.operation_events[0])
        self.assertTrue(dst.operation_event == self.graph.operation_events[0])


if __name__ == '__main__':
    unittest.main()
