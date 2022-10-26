#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from elastic.core.graph.graph import DependencyGraph
from elastic.core.notebook.update_graph import update_graph


class TestUpdateGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph()

    def test_update_graph(self):
        """
            Test graph correctly handles updating from cell code.
        """
        graph = DependencyGraph()
        graph.create_variable_snapshot("x", 1, False)

        update_graph("y = 1\nz = 1", 1, 1, {"x"}, {"y": [0, False], "z": [1, False]}, graph)

        # Check elements have been added to the graph.
        self.assertEqual(len(graph.variable_snapshots["y"]), 1)
        self.assertEqual(len(graph.variable_snapshots["z"]), 1)
        self.assertEqual(len(graph.operation_events), 1)
        self.assertEqual(len(graph.input_nodesets), 1)
        self.assertEqual(len(graph.output_nodesets), 1)

        # Check fields are filled in correctly.
        self.assertEqual(graph.operation_events[0].cell_num, 0)
        self.assertEqual(graph.operation_events[0].cell, "y = 1\nz = 1")
        self.assertEqual(graph.operation_events[0].cell_runtime, 1)
        self.assertEqual(graph.operation_events[0].start_time, 1)
        self.assertEqual(graph.operation_events[0].src, graph.input_nodesets[0])
        self.assertEqual(graph.operation_events[0].dst, graph.output_nodesets[0])


if __name__ == '__main__':
    unittest.main()
