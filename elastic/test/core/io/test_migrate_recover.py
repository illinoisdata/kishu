#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import os
import unittest
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.graph.graph import DependencyGraph
from elastic.test.test_utils import get_test_input_nodeset, get_test_output_nodeset
from elastic.core.io.migrate import migrate
from elastic.core.io.recover import resume

TEST_FILE_PATH = "./tmp_test_file"


class TestMigrateRecover(unittest.TestCase):

    def test_migrate_recover(self):
        """
            Test migrating and recovering a checkpointing configuration preserves all information.
        """
        shell = ZMQInteractiveShell()
        shell.user_ns["x"] = 1
        shell.user_ns["y"] = 1

        # Construct simple test case
        graph = DependencyGraph()
        vs1 = graph.create_variable_snapshot("x", 0, False)
        vs2 = graph.create_variable_snapshot("y", 0, False)
        graph.add_operation_event("", 1, 1, get_test_input_nodeset([]), get_test_output_nodeset([vs1, vs2]))

        vss_to_migrate = {vs1}
        vss_to_recompute = {vs2}
        oes_to_migrate = {graph.operation_events[0]}

        # Migrate the singular variable.
        migrate(graph, shell, vss_to_migrate, vss_to_recompute, oes_to_migrate, TEST_FILE_PATH)
        self.assertTrue(os.path.exists(TEST_FILE_PATH))

        # Recover the checkpoint.
        graph2, variables, vss_to_migrate2, vss_to_recompute2, oes_to_recompute2 = resume(TEST_FILE_PATH)

        # Variable 'x' should be successfully migrated.
        self.assertEqual(1, len(variables[graph2.operation_events[0]]))
        self.assertEqual("x", variables[graph2.operation_events[0]][0][0].name)
        self.assertEqual(1, variables[graph2.operation_events[0]][0][1])

        # Recomputation instructions should be successfully migrated.
        self.assertEqual("x", next(iter(vss_to_migrate2)).name)
        self.assertEqual("y", next(iter(vss_to_recompute2)).name)
        self.assertEqual(0, next(iter(oes_to_recompute2)).cell_num)


if __name__ == '__main__':
    unittest.main()
