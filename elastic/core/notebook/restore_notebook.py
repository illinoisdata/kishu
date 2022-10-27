#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import time

from IPython import get_ipython
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.graph.graph import DependencyGraph


def restore_notebook(graph: DependencyGraph, shell: ZMQInteractiveShell, variables: dict, oes_to_recompute: set,
                     write_log_location=None, notebook_name=None, optimizer_name=None):
    """
        Restores the notebook. Declares variables back into the kernel and recomputes the OEs to restore non-migrated
        variables.
        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            variables (Dict): Mapping from OEs to lists of variables defined in those OEs.
            oes_to_recompute (set): OEs to recompute to restore non-migrated variables.

            write_log_location (str): location to write component runtimes to. For experimentation only.
            notebook_name (str): notebook name. For experimentation only.
            optimizer_name (str): optimizer name. For experimentation only.
    """

    # Recompute OEs following the order they were executed in.
    recompute_start = time.time()
    for oe in graph.operation_events:
        if oe in oes_to_recompute:
            # Rerun cell code
            print("Rerunning cell", oe.cell_num)
            get_ipython().run_cell(oe.cell)
        else:
            # Define output variables in the OE in the order they were defined.
            # i.e. x = 1, y = 2, then we define x followed by y.
            for pair in sorted(variables[oe], key=lambda item: item[0].index):
                print("Declaring variable", pair[0].name)
                shell.user_ns[pair[0].name] = pair[1]

    recompute_end = time.time()
    if write_log_location:
        with open(write_log_location + '/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('Recompute stage took - ' + repr(recompute_end - recompute_start) + " seconds" + '\n')



