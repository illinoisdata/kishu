#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from pathlib import Path

from elastic.io.adapter import Adapter

class ExternalStorage(Adapter):
    def __init__(self):
        self.adapters = {}


    def register(self, scheme: str, adapter: Adapter):
        if scheme not in self.adapters:
            self.adapters[scheme] = adapter
        else:
            raise KeyError("Adapter is already registered for the scheme: {}".format(scheme))


    def select_adapter(self, path) -> Adapter:
        # FIXME: for now, we assume the only adapter is for the local disk
        # this needs to be changed to parse the path for the scheme and return
        # a suitable adapter corresponding to the url (e.g. Azure/GCP storage)
        return self.adapters["local"]


    def read_all(self, path: Path):
        """ExternalStorage selects the adapter that matches the scheme of the path,
        and performs corresponding read_all operation using that matching adapter.

        Args:
            path (Path): schemed path to the file to read
        """
        return self.select_adapter(path).read_all(path)


    def create(self, path: Path):
        """ExternalStorage selects the adapter that matches the scheme of the path,
        and performs corresponding create operation using that matching adapter.

        Args:
            path (Path): schemed path to create a file at
        """
        self.select_adapter(path).create(path)


    def write_all(self, path: Path, buf: bytes):
        """ExternalStorage selects the adapter that matches the scheme of the path,
        and performs corresponding write_all operation using that matching adapter.

        Args:
            path (Path): schemed path to create a file at
            buf (bytes): byte array of data to be written
        """
        self.select_adapter(path).write_all(path, buf)


    def remove(self, path: Path):
        """ExternalStorage selects the adapter that matches the scheme of the path,
        and performs corresponding remove operation using that matching adapter.

        Args:
            path (Path): schemed path to the file to be removed
        """
        self.select_adapter(path).remove(path)
