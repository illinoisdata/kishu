#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from pathlib import Path
import dill

from elastic.core.io.filesystem_adapter import FilesystemAdapter

from elastic.core.io.migrate import FILENAME


def resume(filename: str):
    """
    Reads the file at `filename` and unpacks the graph representation of the notebook, migrated variables, and
    instructions for recomputation.

    Args:
        filename (str): Location of the checkpoint file.
    """

    # Reads from the default location if a file path isn't specified.
    adapter = FilesystemAdapter()
    if filename:
        metadata = dill.loads(adapter.read_all(Path(filename)))
    else:
        metadata = dill.loads(adapter.read_all(Path(FILENAME)))

    return metadata.get_dependency_graph(), metadata.get_variables(), metadata.get_vss_to_migrate(), \
        metadata.get_vss_to_recompute(), metadata.get_oes_to_recompute()
