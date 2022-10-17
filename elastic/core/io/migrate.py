#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import dill
from pathlib import Path
from elastic.core.common.migration_metadata import MigrationMetadata
from elastic.core.graph.graph import DependencyGraph
from elastic.core.globals import variable_version

from elastic.core.io.adapter import Adapter

METADATA_PATH = "./metadata.pickle"


def migrate(dependency_graph: DependencyGraph,
            adapter: Adapter, metadata_path):
    """
    (1) Iterate over all objects and operation events. For each
        (1a) Pickle the object / oe
        (1b) Write to external storage
    (2) Write metadata to external storage

    Args:
        dependency_graph (DependencyGraph):
            the dependency graph to migrate
        adapter (Adapter):
            the location to write the dependency graph and metadata to
    """

    metadata_pickle = dill.dumps(MigrationMetadata().with_dependency_graph(dependency_graph)
                                 .with_variable_version(variable_version))
    if metadata_path:
        print("save to:", metadata_path)
        adapter.write_all(Path(metadata_path), metadata_pickle)
    else:
        adapter.write_all(Path(METADATA_PATH), metadata_pickle)
