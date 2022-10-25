#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
from collections import defaultdict

import dill
from pathlib import Path

from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.common.migration_metadata import MigrationMetadata
from elastic.core.graph.graph import DependencyGraph

from elastic.core.io.filesystem_adapter import FilesystemAdapter

# Default checkpoint location if a file path isn't specified.
FILENAME = "./notebook.pickle"


def migrate(graph: DependencyGraph, shell: ZMQInteractiveShell, vss_to_migrate: set, vss_to_recompute: set,
            oes_to_recompute: set, filename: str):
    """
        Writes the graph representation of the notebook, migrated variables, and instructions for recomputation as the
        specified file.

        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            vss_to_migrate (set): set of VSs to migrate.
            vss_to_recompute (set): set of VSs to recompute.
            oes_to_recompute (set): set of OEs to recompute post-migration.
            filename (str): the location to write the checkpoint to.
    """

    # Retrieve variables to migrate from the current session.
    variables = defaultdict(list)
    for vs in vss_to_migrate:
        variables[vs.output_nodeset.operation_event].append((vs, shell.user_ns[vs.name]))

    # Construct checkpoint JSON.
    adapter = FilesystemAdapter()
    metadata_pickle = dill.dumps(MigrationMetadata().with_dependency_graph(graph)
                                 .with_variables(variables)
                                 .with_vss_to_migrate(vss_to_migrate)
                                 .with_vss_to_recompute(vss_to_recompute)
                                 .with_oes_to_recompute(oes_to_recompute))

    # Write the JSON file to the specified location. Uses the default location if a file path isn't specified.
    if filename:
        print("Checkpoint saved to:", filename)
        adapter.write_all(Path(filename), metadata_pickle)
    else:
        adapter.write_all(Path(FILENAME), metadata_pickle)
