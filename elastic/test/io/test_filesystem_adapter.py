#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import unittest
import os
import pickle
from pathlib import Path

from io.filesystem_adapter import FilesystemAdapter

TEST_FILE_PATH = "./tmp_test_file"
KEY = "project"
VALUE = "elastic-notebook"

class TestFilesystemAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = FilesystemAdapter()
        self.fpath = Path(TEST_FILE_PATH)
    

    def tearDown(self) -> None:
        self.adapter.remove(self.fpath)
        self.assertFalse(os.path.exists(self.fpath))


    def test_create(self):
        self.adapter.create(self.fpath)
        self.assertTrue(os.path.exists(self.fpath))
    
    
    def test_read_write_all(self):
        s = pickle.dumps({KEY: VALUE})
        with open(self.fpath, "wb") as fd:
            fd.write(s)
        
        s_read = self.adapter.read_all(self.fpath)
        self.assertEqual(VALUE, pickle.loads(s_read)[KEY])
        
        s = pickle.dumps({VALUE: KEY})
        self.adapter.write_all(self.fpath, s)
        
        with open(self.fpath, "rb") as fd:
            s_read = pickle.loads(fd.read())
        self.assertEqual(1, len(s_read))
        self.assertEqual(KEY, s_read[VALUE])
        

if __name__ == '__main__':
    unittest.main()
