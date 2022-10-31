#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import os
import unittest

from IPython.terminal.interactiveshell import TerminalInteractiveShell
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.notebook.find_input_output_vars import find_input_output_vars
from elastic.test.test_utils import get_test_input_nodeset, get_test_output_nodeset, get_problem_setting
from elastic.core.notebook.checkpoint import checkpoint
from elastic.algorithm.baseline import MigrateAllBaseline
from elastic.core.io.recover import resume

TEST_FILE_PATH = "./tmp_test_file"


class TestFindInputOutputVars(unittest.TestCase):
    def setUp(self) -> None:
        self.shell = TerminalInteractiveShell.instance()

    def test_simple_case(self):
        """
            Test input and output variables are correctly identified.
        """
        self.shell.user_ns["x"] = 1
        self.shell.user_ns["y"] = 1

        input_vars, output_vars = find_input_output_vars("y = x", {"x"}, self.shell, [])

        # x is an input and y is an output.
        self.assertEqual({"x"}, input_vars)
        self.assertEqual({"y"}, set(output_vars.keys()))

        # y is the first defined variable in the cell and is not deleted.
        self.assertEqual(0, output_vars["y"][0])
        self.assertEqual(False, output_vars["y"][1])

    def test_skip_builtin(self):
        """
            Test builtin items (i.e. not defined by the user in the current session) are not captured.
        """
        self.shell.user_ns["x"] = [1]
        self.shell.user_ns["y"] = 1

        input_vars, output_vars = find_input_output_vars("y = len(x)", {"x"}, self.shell, [])

        # x is an input and y is an output. 'len' is not an input.
        self.assertEqual({"x"}, input_vars)
        self.assertEqual({"x", "y"}, set(output_vars.keys()))

    def test_order(self):
        """
            Test variable definition order being captured correctly.
        """
        self.shell.user_ns["x"] = 1
        self.shell.user_ns["y"] = 1
        self.shell.user_ns["z"] = 2

        input_vars, output_vars = find_input_output_vars("y = x\nz = x + 1", {"x"}, self.shell, [])

        # x is an input and y is an output. 'len' is not an input.
        self.assertEqual({"x"}, input_vars)
        self.assertEqual({"y", "z"}, set(output_vars.keys()))

        # y is the first defined variable in the cell and z is second.
        self.assertEqual(0, output_vars["y"][0])
        self.assertEqual(1, output_vars["z"][0])

    def test_delete(self):
        """
            Test deletion of variable marked correctly.
        """
        input_vars, output_vars = find_input_output_vars("del x", {"x"}, self.shell, [])

        # x is an output.
        self.assertEqual(set(output_vars.keys()), {"x"})

        # x has been deleted.
        self.assertEqual(0, output_vars["x"][0])
        self.assertEqual(True, output_vars["x"][1])

    def test_recover(self):
        """
            Test declaring a deleted variable in the same cell un-marks the deletion flag.
        """
        self.shell.user_ns["x"] = 1

        input_vars, output_vars = find_input_output_vars("del x\nx = 1", {"x"}, self.shell, [])

        # x is an output.
        self.assertEqual(set(output_vars.keys()), {"x"})

        # x has been deleted then re-declared.
        self.assertEqual(0, output_vars["x"][0])
        self.assertEqual(False, output_vars["x"][1])

    def test_modify(self):
        """
            Test modifying a variable in the cell marks it as both an input and an output.
        """
        self.shell.user_ns["x"] = 2

        input_vars, output_vars = find_input_output_vars("x += 1", {"x"}, self.shell, [])

        # x is modified; it is both an input and an output.
        self.assertEqual({"x"}, set(input_vars))
        self.assertEqual({"x"}, set(output_vars.keys()))

    def test_declare_and_modify(self):
        """
            Test a variable declared and modified in the same cell is not marked as an input.
        """
        self.shell.user_ns["y"] = 1
        self.shell.user_ns["z"] = 1

        input_vars, output_vars = find_input_output_vars("y = 1\nz = y", {"x"}, self.shell, [])

        # y should only be an output of the cell.
        self.assertEqual(set(), set(input_vars))
        self.assertEqual({"y", "z"}, set(output_vars.keys()))

    def test_inplace_method(self):
        """
            Test a class method call is correctly identified as a modification.
        """
        self.shell.user_ns["x"] = [1]
        self.shell.user_ns["s"] = "str"

        input_vars, output_vars = find_input_output_vars("x.reverse()\ns.strip()", {"x", "s"}, self.shell, [])

        # x is not a primitive, so it can potentially be modified; it is both an input and an output.
        self.assertEqual({"x", "s"}, set(input_vars))
        self.assertEqual({"x"}, set(output_vars.keys()))

    def test_pass_to_function(self):
        """
            Test passing a variable to a function is correctly identified as a modification.
        """
        self.shell.user_ns["x"] = [1]
        self.shell.user_ns["s"] = "str"

        input_vars, output_vars = find_input_output_vars("print(x)\nprint(s)", {"x", "s"}, self.shell, [])

        # x is not a primitive, so it can potentially be modified; it is both an input and an output.
        self.assertEqual({"x", "s"}, set(input_vars))
        self.assertEqual({"x"}, set(output_vars.keys()))

    def test_error(self):
        """
            Test correct identification of error line number and skipping of subsequent code.
        """
        self.shell.user_ns["x"] = 1
        self.shell.user_ns["y"] = 1
        traceback_str = """
            File "/var/folders/t9/7bppp22j4nq50851rm2rb7780000gn/T/ipykernel_5202/3652387590.py", line 2, in <module>
            print(nonexistent_variable)
        """
        input_vars, output_vars = find_input_output_vars(
            "y = x\nprint(nonexistent_variable)\nz = x", {"x"}, self.shell, [traceback_str])

        # Since the code stopped on line 2 (print(nonexistent_variable)), z was never assigned.
        self.assertEqual({"x"}, set(input_vars))
        self.assertEqual({"y"}, set(output_vars.keys()))


if __name__ == '__main__':
    unittest.main()
