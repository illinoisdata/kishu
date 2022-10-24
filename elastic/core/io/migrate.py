#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
from collections import defaultdict

import dill
from pathlib import Path
from elastic.core.common.migration_metadata import MigrationMetadata
from elastic.core.graph.graph import DependencyGraph

from elastic.core.io.adapter import Adapter
from elastic.core.io.filesystem_adapter import FilesystemAdapter

FILENAME = "./notebook.pickle"


def migrate(graph, shell, vss_to_migrate, vss_to_recompute, oes_to_recompute, filename):
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
    # Retrieve variables
    variables = defaultdict(list)
    for vs in vss_to_migrate:
        variables[vs.output_nodeset.operation_event].append((vs, shell.user_ns[vs.name]))

    adapter = FilesystemAdapter()
    metadata_pickle = dill.dumps(MigrationMetadata().with_dependency_graph(graph)
                                 .with_variables(variables)
                                 .with_vss_to_migrate(vss_to_migrate)
                                 .with_vss_to_recompute(vss_to_recompute)
                                 .with_oes_to_recompute(oes_to_recompute))

    if filename:
        print("Checkpoint saved to:", filename)
        adapter.write_all(Path(filename), metadata_pickle)
    else:
        adapter.write_all(Path(FILENAME), metadata_pickle)
