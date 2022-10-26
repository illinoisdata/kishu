import unittest

import os, sys

from elastic.test.test_utils import get_problem_setting
from elastic.algorithm.optimizer_greedy import OptimizerGreedy


class TestOptimizerGreedy(unittest.TestCase):
    def test_optimizer_local_min(self):
        # Setup problem
        opt = OptimizerGreedy(migration_speed_bps=1)
        graph, active_vss = get_problem_setting()
        opt.dependency_graph = graph
        opt.active_vss = active_vss

        # Tests that the greedy optimizer does not escape the local minimum and migrates both x and y.
        vss_to_migrate = opt.select_vss()
        self.assertEqual(vss_to_migrate, {graph.variable_snapshots["x"][0], graph.variable_snapshots["y"][0]})

    def test_optimizer_success(self):
        # Setup problem
        opt = OptimizerGreedy(migration_speed_bps=1)
        graph, active_vss = get_problem_setting()
        opt.dependency_graph = graph
        opt.active_vss = active_vss

        # Adjust problem so un-migrating x or y has net 0 gain on checkpointing cost.
        graph.operation_events[0].cell_runtime = 1.9

        # Tests that the greedy optimizer now correctly recomputes both x and y.
        vss_to_migrate = opt.select_vss()
        self.assertEqual(vss_to_migrate, set())


if __name__ == '__main__':
    unittest.main()
