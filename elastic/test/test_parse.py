#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import os
import pytest

from IPython.terminal.interactiveshell import TerminalInteractiveShell
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.test.test_utils import get_test_input_nodeset, get_test_output_nodeset, get_problem_setting
from elastic.core.notebook.checkpoint import checkpoint
from elastic.algorithm.baseline import MigrateAllBaseline
from elastic.core.io.recover import resume
from elastic.parse.parse import identify_vars

TEST_FILE_PATH = "./tmp_test_file"

shell = TerminalInteractiveShell.instance()

def testBasicDecleration():
    """
    a = 1
    """
    vars = identify_vars("a = 1", shell, ())
    # x is an input and y is an output.
    assert {'a'} == vars

def testMultipleVariableDecleration():
    """
    a = 1
    b = 3
    c = a + b
    """
    vars = identify_vars("a = 1\nb = 3\nc = a + b", shell, ())
    # x is an input and y is an output.
    assert {'a', 'b', 'c'} == vars

def testLibraryImport():
    """
    import numpy as np
    a = np.zeros((2,2))
    b = a + 1
    """

    vars = identify_vars("a = np.zeros((2,2))\nb = a + 1", shell, ())
    # x is an input and y is an output.
    assert {'np', 'a', 'b'} == vars

def testSimpleFunctionCall():
    """
    def foo(item):
        mylist.append(item)     # accessing a global variable "mylist"
    item = 3
    foo(item)
    """
    vars = identify_vars("def foo(item):\n\tmylist.append(item)\nitem = 3\nfoo(item)", shell, ())
    # x is an input and y is an output.
    assert {'foo', 'mylist', 'item'} == vars

def testNestedFunctionCall():
    """
    def goo(item1):
        mylist2.append(item)     # accessing a global variable "mylist2"

    def foo(item2):
        mylist.append(item)     # accessing a global variable "mylist"
        goo(item2)
    foo(3)
    """
    vars = identify_vars("def goo(item):\n\tmylist2.append(item)\ndef foo(item):\n\tmylist.append(item)  \
                            \n\tgoo(item)\nfoo(3)", shell, ())
    # x is an input and y is an output.
    assert {'foo', 'goo', 'mylist', 'mylist2'} == vars

def testRecursiveFunctionCall():
    """
    def foo(item):
        if random.random() < 0.5:
            mylist.append(item)     # accessing a global variable "mylist"
            return
        foo(item)
    foo(3)
    """
    vars = identify_vars("def foo(item):\n\tif random.random() < 0.5:\n\t\tmylist.append(item)\n\t\treturn \
                        \n\tfoo(item)\nfoo(3)", shell, ())
    # x is an input and y is an output.
    assert {'foo', 'mylist', 'random'} == vars

def testShellVariables():
    """
    def foo(item):
        temp = "test"
    foo(3)
    """
    shell.user_ns["temp"] = "tmpstr"
    shell.user_ns["item"] = 1
    vars = identify_vars("def foo(item):\n\ttemp = 3\nfoo(3)", shell, ())
    # x is an input and y is an output.
    assert {'foo', 'temp'} == vars

def testShellFunction():
    """
    def goo(var):
        g1 += var
        g2 = "tempstr"
    def foo(item):
        goo(item / 3)
    foo(g3)
    """

    shell.user_ns["goo"] = goo
    shell.user_ns["g1"] = 1
    shell.user_ns["g2"] = "hi"
    shell.user_ns["g3"] = 2
    vars = identify_vars("def foo(item):\n\tgoo(item / 3)\nfoo(g3)", shell, ("goo"))
    # x is an input and y is an output.
    assert {'foo', 'goo', 'g1', 'g2', 'g3'} == vars



# User Defined functions
def goo(var):
    g1 += var
    g2 = "tempstr"
