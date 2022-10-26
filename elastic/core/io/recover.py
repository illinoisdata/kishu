#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import time
from pathlib import Path
import dill

from elastic.core.io.filesystem_adapter import FilesystemAdapter

from elastic.core.io.migrate import FILENAME


def resume(filename: str, write_log_location=None, notebook_name=None, optimizer_name=None):
    """
    Reads the file at `filename` and unpacks the graph representation of the notebook, migrated variables, and
    instructions for recomputation.

    Args:
        filename (str): Location of the checkpoint file.

        write_log_location (str): location to write file read runtime to. For experimentation only.
        notebook_name (str): notebook name. For experimentation only.
        optimizer_name (str): optimizer name. For experimentation only.
    """

    # Reads from the default location if a file path isn't specified.
    adapter = FilesystemAdapter()

    load_start = time.time()
    if filename:
        metadata = dill.loads(adapter.read_all(Path(filename)))
    else:
        metadata = dill.loads(adapter.read_all(Path(FILENAME)))
    load_end = time.time()

    if write_log_location:
        with open('results/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('Reload stage took - ' + repr(load_end - load_start) + " seconds" + '\\n')

    return metadata.get_dependency_graph(), metadata.get_variables(), metadata.get_vss_to_migrate(), \
        metadata.get_vss_to_recompute(), metadata.get_oes_to_recompute()
