#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import sys

from elastic.algorithm.optimizer_exact import OptimizerExact
from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.find_oes_to_recompute import find_oes_to_recompute
from elastic.core.io.migrate import migrate


# Writes the notebook state to the specified filename.
def checkpoint(graph: DependencyGraph, shell, filename):
    """
    TODO: measure the disk I/O speed to 'filename' at checkpoint time.
    Migration_speed_bps should be the sum of read and write speed (since we are writing the state to disk, then
    reading from disk to restore the notebook).
    """
    migration_speed_bps = 100000
    selector = OptimizerExact(migration_speed_bps=migration_speed_bps)

    # Active VSs are correspond to the latest instances/versions of each variable.
    active_vss = []
    for vs_list in graph.variable_snapshots.values():
        if not vs_list[-1].deleted:
            active_vss.append(vs_list[-1])

    # Estimate the size of each active vs.
    for active_vs in active_vss:
        active_vs.size = sys.getsizeof(shell.user_ns[active_vs.name])

    selector.dependency_graph = graph
    selector.active_vss = active_vss
    vss_to_migrate = selector.select_nodes()

    print("---------------------------")
    print("variables to migrate:")
    for vs in vss_to_migrate:
        print(vs.name, vs.size)

    vss_to_recompute = set(active_vss) - set(vss_to_migrate)
    print("---------------------------")
    print("variables to recompute:")
    for vs in vss_to_recompute:
        print(vs.name, vs.size)

    oes_to_recompute = find_oes_to_recompute(graph, vss_to_migrate, vss_to_recompute)
    print("---------------------------")
    print("OEs to recompute:")
    for oe in oes_to_recompute:
        print(oe.cell_num, oe.duration)

    migrate(graph, shell, vss_to_migrate, vss_to_recompute, oes_to_recompute, filename)
