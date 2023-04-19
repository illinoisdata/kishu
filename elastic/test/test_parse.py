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
from elastic.parse.parse import identify_vars

TEST_FILE_PATH = "./tmp_test_file"


class TestParse(unittest.TestCase):
    def setUp(self) -> None:
        self.shell = TerminalInteractiveShell.instance()
    def testBasicDecleration(self):
        """
        a = 1
        """
        vars = identify_vars("a = 1", self.shell, ())
        # x is an input and y is an output.
        self.assertEqual({'a'}, vars)

    def testMultipleVariableDecleration(self):
        """
        a = 1
        b = 3
        c = a + b
        """
        vars = identify_vars("a = 1\nb = 3\nc = a + b", self.shell, ())
        # x is an input and y is an output.
        self.assertEqual({'a', 'b', 'c'}, vars)

    def testLibraryImport(self):
        """
        import numpy as np
        a = np.zeros((2,2))
        b = a + 1
        """

        vars = identify_vars("a = np.zeros((2,2))\nb = a + 1", self.shell, ())
        # x is an input and y is an output.
        self.assertEqual({'np', 'a', 'b'}, vars)

    def testSimpleFunctionCall(self):
        """
        def foo(item):
            mylist.append(item)     # accessing a global variable "mylist"
        item = 3
        foo(item)
        """
        vars = identify_vars("def foo(item):\n\tmylist.append(item)\nitem = 3\nfoo(item)", self.shell, ())
        # x is an input and y is an output.
        self.assertEqual({'foo', 'mylist', 'item'}, vars)

    def testNestedFunctionCall(self):
        """
        def goo(item):
            mylist2.append(item)     # accessing a global variable "mylist2"

        def foo(item):
            mylist.append(item)     # accessing a global variable "mylist"
            goo(item)
        foo(3)
        """
        vars = identify_vars("def goo(item):\n\tmylist2.append(item)\ndef foo(item):\n\tmylist.append(item)  \
                                \n\tgoo(item)\nfoo(3)", self.shell, ())
        # x is an input and y is an output.
        self.assertEqual({'foo', 'goo', 'mylist', 'mylist2'}, vars)
    
    def testRecursiveFunctionCall(self):
        """
        def foo(item):
            if random.random() < 0.5:
                mylist.append(item)     # accessing a global variable "mylist"
                return
            foo(item)
        foo(3)
        """
        vars = identify_vars("def foo(item):\n\tif random.random() < 0.5:\n\t\tmylist.append(item)\n\t\treturn \
                            \n\tfoo(item)\nfoo(3)", self.shell, ())
        # x is an input and y is an output.
        self.assertEqual({'foo', 'mylist', 'random'}, vars)

    def testShellVariables(self):
        """
        def foo(item):
            temp = "test"
        foo(3)
        """
        self.shell.user_ns["temp"] = "tmpstr"
        self.shell.user_ns["item"] = 1
        vars = identify_vars("def foo(item):\n\ttemp = 3\nfoo(3)", self.shell, ())
        # x is an input and y is an output.
        self.assertEqual({'foo', 'temp'}, vars)

    def testShellFunction(self):
        """
        def goo(var):
            g1 += var
            g2 = "tempstr"
        def foo(item):
            goo(item / 3)
        foo(g3)
        """

        self.shell.user_ns["goo"] = goo
        self.shell.user_ns["g1"] = 1
        self.shell.user_ns["g2"] = "hi"
        self.shell.user_ns["g3"] = 2
        vars = identify_vars("def foo(item):\n\tgoo(item / 3)\nfoo(g3)", self.shell, ("goo"))
        # x is an input and y is an output.
        self.assertEqual({'foo', 'goo', 'g1', 'g2', 'g3'}, vars)

if __name__ == '__main__':
    unittest.main()


# User Defined functions
def goo(var):
    g1 += var
    g2 = "tempstr"
