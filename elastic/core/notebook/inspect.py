#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois


from elastic.core.graph.graph import DependencyGraph


def inspect(graph: DependencyGraph):
    """
        Displays the graph structure of the current notebook state.
        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
    """

    print("---------------------------")
    print("VSs:")
    for vs_list in graph.variable_snapshots.values():
        for vs in vs_list:
            print(vs.name, vs.version)

    print("---------------------------")
    print("OEs:")
    for oe in graph.operation_events:
        print("---------------------------")
        print("OE num:", oe.cell_num, " runtime:", oe.cell_runtime)
        print("sources")
        for vs in oe.src.vs_list:
            print("   ", vs.name, vs.version)
        print("destinations")
        for vs in oe.dst.vs_list:
            print("   ", vs.name, vs.version)
