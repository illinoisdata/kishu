#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.io.external_storage import ExternalStorage
from core.io.filesystem_adapter import FilesystemAdapter
from experiment.recover import resume


def main():
    storage = ExternalStorage()
    storage.register("local", FilesystemAdapter())
    
    resume(storage, globals())


if __name__ == '__main__':
    main()
