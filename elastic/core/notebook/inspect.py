#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import networkx as nx
from matplotlib import pyplot as plt

from elastic.core.graph.graph import DependencyGraph


def inspect(graph: DependencyGraph):
    """
        Displays the graph structure of the current notebook state.
        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
    """

    # Graph to display.
    display_graph = nx.DiGraph()

    # Dict of nodeset objects to string representation of nodeset contents.
    nodeset_dict = {}

    # Add string representation of nodesets.
    for nodeset in graph.input_nodesets + graph.output_nodesets:
        nodeset_str = ""
        for vs in nodeset.vs_list:
            nodeset_str += "(" + vs.name + "," + str(vs.version) + "),"
        # Trim the trailing comma
        if len(nodeset_str) > 0:
            nodeset_str = nodeset_str[:-1]
        nodeset_dict[nodeset] = nodeset_str
        display_graph.add_node(nodeset_str)

    # Add string representation of OEs.
    for oe in graph.operation_events:
        display_graph.add_edge(nodeset_dict[oe.src], nodeset_dict[oe.dst], cell=str(oe.cell_num))

    # Add inter-cell dependencies.
    for dst in graph.output_nodesets:
        for src in graph.input_nodesets:
            if set(dst.vs_list).intersection(set(src.vs_list)):
                display_graph.add_edge(nodeset_dict[dst], nodeset_dict[src])

    # Draw the graph.
    pos = nx.spring_layout(display_graph)
    nx.draw_networkx(display_graph, pos, with_labels = True)
    nx.draw_networkx_edge_labels(display_graph, pos)

    plt.show()
