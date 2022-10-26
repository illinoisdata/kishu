#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import time

from elastic.algorithm.selector import Selector
from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.find_oes_to_recompute import find_oes_to_recompute
from elastic.core.io.migrate import migrate
from elastic.core.common.profile_variable_size import profile_variable_size
from ipykernel.zmqshell import ZMQInteractiveShell


def checkpoint(graph: DependencyGraph, shell: ZMQInteractiveShell, selector: Selector, filename: str,
               write_log_location=None, notebook_name=None, optimizer_name=None):
    """
        Checkpoints the notebook. The optimizer selects the VSs to migrate and recompute and the OEs to recompute, then
        writes the checkpoint as the specified filename.
        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            selector (Selector): optimizer for computing the checkpointing configuration.
            filename (str): location to write the file to.

            write_log_location (str): location to write component runtimes to. For experimentation only.
            notebook_name (str): notebook name. For experimentation only.
            optimizer_name (str): optimizer name. For experimentation only.
    """

    # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
    active_vss = []
    for vs_list in graph.variable_snapshots.values():
        if not vs_list[-1].deleted:
            active_vss.append(vs_list[-1])

    # Profile the size of each variable defined in the current session.
    for active_vs in active_vss:
        active_vs.size = profile_variable_size(shell.user_ns[active_vs.name])

    # Initialize the optimizer.
    selector.dependency_graph = graph
    selector.active_vss = active_vss

    # Use the optimizer to compute the checkpointing configuration.
    optimize_start = time.time()
    vss_to_migrate = selector.select_vss()
    optimize_end = time.time()

    if write_log_location:
        with open('results/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('\\nOptimize stage took - ' + repr(optimize_end - optimize_start) + " seconds" + '\\n')

    print("---------------------------")
    print("variables to migrate:")
    for vs in vss_to_migrate:
        print(vs.name, vs.size)

    vss_to_recompute = set(active_vss) - set(vss_to_migrate)

    print("---------------------------")
    print("variables to recompute:")
    for vs in vss_to_recompute:
        print(vs.name, vs.size)

    # Find OEs to recompute via BFS from VSs to recompute.
    oes_to_recompute = find_oes_to_recompute(vss_to_migrate, vss_to_recompute)

    print("---------------------------")
    print("OEs to recompute:")
    for oe in oes_to_recompute:
        print(oe.cell_num, oe.cell_runtime)

    # Store the notebook checkpoint to the specified location.
    migrate_start = time.time()
    migrate(graph, shell, vss_to_migrate, vss_to_recompute, oes_to_recompute, filename)
    migrate_end = time.time()

    if write_log_location:
        with open('results/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('Migrate stage took - ' + repr(migrate_end - migrate_start) + " seconds" + '\\n')
