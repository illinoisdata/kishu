import unittest

from elastic.algorithm.optimizer_exact import OptimizerExact
from elastic.test.test_utils import get_problem_setting


class TestOptimizerExact(unittest.TestCase):
    def test_optimizer(self):
        # Setup problem
        opt = OptimizerExact(migration_speed_bps=1)
        graph, active_vss = get_problem_setting()
        opt.dependency_graph = graph
        opt.active_vss = active_vss

        # Tests that the exact optimizer correctly escapes the local minimum by recomputing both x and y.
        vss_to_migrate = opt.select_vss()
        self.assertEqual(set(), vss_to_migrate)


if __name__ == '__main__':
    unittest.main()
