#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest

import os
import subprocess
import types

from elastic.core.globals import operation_events
from elastic.core.notebook.update_graph import RecordEvent

@RecordEvent
def TEST_FUNC():
    return "a"


class TestOperationEvent(unittest.TestCase):
    def test_source_code_inspect(self):
        TEST_FUNC()
        self.assertEqual(1, len(operation_events))

        # verify that captured source code matches
        func = types.FunctionType(operation_events[0].cell_func_code, globals(), "test")
        self.assertEqual(func(), "a")

if __name__ == '__main__':
    unittest.main()
