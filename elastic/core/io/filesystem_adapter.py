#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from pathlib import Path

from core.io.adapter import Adapter

class FilesystemAdapter(Adapter):
    def __init__(self):
        pass


    def read_all(self, path: Path):
        return path.read_bytes()


    def create(self, path: Path):
        path.touch()


    def write_all(self, path: Path, buf: bytes):
        path.write_bytes(buf)


    def remove(self, path: Path):
        path.unlink()
