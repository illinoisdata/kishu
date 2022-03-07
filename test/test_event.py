#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest

import os
import subprocess

from elastic.container import operation_events
from elastic.record_event import RecordEvent

@RecordEvent
def TEST_FUNC():
    pass

TEST_FILE_NAME = 'test_func.py'


class TestOperationEvent(unittest.TestCase):
    def test_source_code_inspect(self):
        TEST_FUNC()
        self.assertEqual(1, len(operation_events))
        # verify that captured source code matches
        self.assertEqual('@RecordEvent\ndef TEST_FUNC():\n    pass\n', 
                         operation_events[0].cell_func_code)
        
        # verify that captured source code can be reconstructed
        with open(TEST_FILE_NAME, 'w') as fd:
            fd.write("from elastic.record_event import RecordEvent\n")
            fd.write(operation_events[0].cell_func_code)
        
        subprocess.call(TEST_FILE_NAME, shell=True) # saved code executed without issue
        os.remove(TEST_FILE_NAME)
        

if __name__ == '__main__':
    unittest.main()
