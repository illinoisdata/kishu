#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import sys

from elastic.algorithm.selector import Selector
from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.find_oes_to_recompute import find_oes_to_recompute
from elastic.core.io.migrate import migrate
from ipykernel.zmqshell import ZMQInteractiveShell


def checkpoint(graph: DependencyGraph, shell: ZMQInteractiveShell, selector: Selector, filename: str):
    """
        Checkpoints the notebook. The optimizer selects the VSs to migrate and recompute and the OEs to recompute, then
        writes the checkpoint as the specified filename.
        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            selector (Selector): optimizer for computing the checkpointing configuration.
            filename (str): location to write the file to.
    """

    # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
    active_vss = []
    for vs_list in graph.variable_snapshots.values():
        if not vs_list[-1].deleted:
            active_vss.append(vs_list[-1])

    """
    TODO: replace sys.getsizeof with a more accurate estimation function.
    sys.getsizeof notably does not work well with nested structures (i.e. lists, dictionaries).
    """
    # Profile the size of each variable defined in the current session.
    for active_vs in active_vss:
        active_vs.size = sys.getsizeof(shell.user_ns[active_vs.name])

    # Use the optimizer to compute the checkpointing configuration.
    selector.dependency_graph = graph
    selector.active_vss = active_vss
    vss_to_migrate = selector.select_vss()

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
    migrate(graph, shell, vss_to_migrate, vss_to_recompute, oes_to_recompute, filename)
