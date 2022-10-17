#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from pathlib import Path
import dill

from elastic.core.io.adapter import Adapter

from elastic.core.io.migrate import METADATA_PATH
import elastic.core.globals


def resume(adapter: Adapter, metadata_path):
    """
    Reads the file at `migration_metadata_path` in `storage` and unpacks global variables and dependency graph.

    Args:
        adapter (Adapter):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
    """
    if metadata_path:
        metadata = dill.loads(adapter.read_all(Path(metadata_path)))
    else:
        metadata = dill.loads(adapter.read_all(Path(METADATA_PATH)))

    elastic.core.globals.variable_version = metadata.get_variable_version()
    return metadata.get_dependency_graph()



