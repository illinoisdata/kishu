#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from pathlib import Path
import dill

from core.io.adapter import Adapter

from core.io.migrate import METADATA_PATH
import core.globals


def resume(adapter: Adapter):
    """
    Reads the file at `migration_metadata_path` in `storage` and unpacks global variables and dependency graph.

    Args:
        adapter (Adapter):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
    """
    metadata = dill.loads(adapter.read_all(Path(METADATA_PATH)))

    core.globals.variable_version = metadata.get_variable_version()
    return metadata.get_dependency_graph()



