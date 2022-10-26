#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
from elastic.core.graph.find_oes_to_recompute import find_oes_to_recompute
from elastic.test.test_utils import get_test_vs, get_test_oe, get_test_input_nodeset, get_test_output_nodeset


class TestFindOesToRecompute(unittest.TestCase):
    
    def test_find_path_empty_graph(self):
        """
            Test function works for empty graph.
        """
        oes_to_recompute = find_oes_to_recompute(set(), set())
        self.assertEqual(0, len(oes_to_recompute))
        
    def test_find_path_two_nodesets(self):
        """
            Test function works for simple single cell execution.
        """
        vs = get_test_vs("x")
        src = get_test_input_nodeset([])
        dst = get_test_output_nodeset([vs])
        oe = get_test_oe(1, src=src, dst=dst)
        src.operation_event = oe
        dst.operation_event = oe

        oes_to_recompute = find_oes_to_recompute(set(), {vs})
        self.assertEqual({oe}, oes_to_recompute)
    
    def test_find_path_multiple_edges(self):
        """
            Test function BFS works for more complicated problem settings.
        """
        vs1 = get_test_vs("x")
        vs2 = get_test_vs("y")
        vs3 = get_test_vs("z")

        src1 = get_test_input_nodeset([])
        dst1 = get_test_output_nodeset([vs1])
        oe1 = get_test_oe(1, src=src1, dst=dst1)
        src1.operation_event = oe1
        dst1.operation_event = oe1

        src2 = get_test_input_nodeset([vs1])
        dst2 = get_test_output_nodeset([vs2, vs3])
        oe2 = get_test_oe(1, src=src2, dst=dst2)
        src2.operation_event = oe2
        dst2.operation_event = oe2

        oes_to_recompute = find_oes_to_recompute({vs1}, {vs2, vs3})
        self.assertEqual({oe2}, oes_to_recompute)  # both vars in dst2 need to be recomputed

        oes_to_recompute = find_oes_to_recompute({vs3}, {vs1, vs2})
        self.assertEqual({oe1, oe2}, oes_to_recompute)  # 1 var in dst1 and 1 var in dst2 need to be recomputed

        oes_to_recompute = find_oes_to_recompute({}, {vs2, vs3})
        self.assertEqual({oe1, oe2}, oes_to_recompute)  # recomputing y and z require rerunning both cells


if __name__ == '__main__':
    unittest.main()
