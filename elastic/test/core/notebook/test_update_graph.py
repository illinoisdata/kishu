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
        self.assertEqual(1, len(graph.variable_snapshots["y"]))
        self.assertEqual(1, len(graph.variable_snapshots["z"]))
        self.assertEqual(1, len(graph.operation_events))
        self.assertEqual(1, len(graph.input_nodesets))
        self.assertEqual(1, len(graph.output_nodesets))

        # Check fields are filled in correctly.
        self.assertEqual(0, graph.operation_events[0].cell_num)
        self.assertEqual("y = 1\nz = 1", graph.operation_events[0].cell)
        self.assertEqual(1, graph.operation_events[0].cell_runtime)
        self.assertEqual(1, graph.operation_events[0].start_time)
        self.assertTrue(graph.input_nodesets[0] == graph.operation_events[0].src)
        self.assertTrue(graph.output_nodesets[0] == graph.operation_events[0].dst)


if __name__ == '__main__':
    unittest.main()
