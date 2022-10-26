#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import os
import unittest
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.notebook.find_input_output_vars import find_input_output_vars
from elastic.test.test_utils import get_test_input_nodeset, get_test_output_nodeset, get_problem_setting
from elastic.core.notebook.checkpoint import checkpoint
from elastic.algorithm.baseline import MigrateAllBaseline
from elastic.core.io.recover import resume

TEST_FILE_PATH = "./tmp_test_file"


class TestFindInputOutputVars(unittest.TestCase):

    def test_simple_case(self):
        """
            Test input and output variables are correctly identified.
        """
        input_vars, output_vars = find_input_output_vars("y = x", {"x"}, [])

        # x is an input and y is an output.
        self.assertEqual(input_vars, {"x"})
        self.assertEqual(set(output_vars.keys()), {"y"})

        # y is the first defined variable in the cell and is not deleted.
        self.assertEqual(output_vars["y"][0], 0)
        self.assertEqual(output_vars["y"][1], False)

    def test_skip_builtin(self):
        """
            Test builtin items (i.e. not defined by the user in the current session) are not captured.
        """
        input_vars, output_vars = find_input_output_vars("y = len(x)", {"x"}, [])

        # x is an input and y is an output. 'len' is not an input.
        self.assertEqual(input_vars, {"x"})
        self.assertEqual(set(output_vars.keys()), {"y"})

    def test_order(self):
        """
            Test variable definition order being captured correctly.
        """
        input_vars, output_vars = find_input_output_vars("y = x\nz = x + 1", {"x"}, [])

        # x is an input and y is an output. 'len' is not an input.
        self.assertEqual(input_vars, {"x"})
        self.assertEqual(set(output_vars.keys()), {"y", "z"})

        # y is the first defined variable in the cell and z is second.
        self.assertEqual(output_vars["y"][0], 0)
        self.assertEqual(output_vars["z"][0], 1)

    def test_delete(self):
        """
            Test deletion of variable marked correctly.
        """
        input_vars, output_vars = find_input_output_vars("del x", {"x"}, [])

        # x is an output.
        self.assertEqual(set(output_vars.keys()), {"x"})

        # x has been deleted.
        self.assertEqual(output_vars["x"][0], 0)
        self.assertEqual(output_vars["x"][1], True)

    def test_recover(self):
        """
            Test declaring a deleted variable in the same cell un-marks the deletion flag.
        """
        input_vars, output_vars = find_input_output_vars("del x\nx = 1", {"x"}, [])

        # x is an output.
        self.assertEqual(set(output_vars.keys()), {"x"})

        # x has been deleted then re-declared.
        self.assertEqual(output_vars["x"][0], 0)
        self.assertEqual(output_vars["x"][1], False)

    def test_modify(self):
        """
            Test modifying a variable in the cell marks it as both an input and an output.
        """
        input_vars, output_vars = find_input_output_vars("x += 1", {"x"}, [])

        # x is modified; it is both an input and an output.
        self.assertEqual(set(input_vars), {"x"})
        self.assertEqual(set(output_vars.keys()), {"x"})

    def test_declare_and_modify(self):
        """
            Test a variable declared and modified in the same cell is not marked as an input.
        """
        input_vars, output_vars = find_input_output_vars("y = 1\nz = y", {"x"}, [])

        # y should only be an output of the cell.
        self.assertEqual(set(input_vars), set())
        self.assertEqual(set(output_vars.keys()), {"y", "z"})

    def test_inplace_method(self):
        """
            Test a class method call is correctly identified as a modification.
        """
        input_vars, output_vars = find_input_output_vars("x.reverse()", {"x"}, [])

        # x is modified; it is both an input and an output.
        self.assertEqual(set(input_vars), set("x"))
        self.assertEqual(set(output_vars.keys()), {"x"})

    def test_pass_to_function(self):
        """
            Test passing a variable to a function is correctly identified as a modification.
        """
        input_vars, output_vars = find_input_output_vars("print(x)", {"x"}, [])

        # x is modified; it is both an input and an output.
        self.assertEqual(set(input_vars), set("x"))
        self.assertEqual(set(output_vars.keys()), {"x"})

    def test_error(self):
        """
            Test correct identification of error line number and skipping of subsequent code.
        """
        traceback_str = """
            File "/var/folders/t9/7bppp22j4nq50851rm2rb7780000gn/T/ipykernel_5202/3652387590.py", line 2, in <module>
            print(nonexistent_variable)
        """
        input_vars, output_vars = find_input_output_vars(
            "y = x\nprint(nonexistent_variable)\nz = x", {"x"}, [traceback_str])

        # Since the code stopped on line 2 (print(aaa)), z was never assigned.
        self.assertEqual(set(input_vars), set("x"))
        self.assertEqual(set(output_vars.keys()), {"y"})


if __name__ == '__main__':
    unittest.main()
