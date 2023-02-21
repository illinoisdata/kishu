#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import networkx as nx
from matplotlib import pyplot as plt
import pylab as plt
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
# import pygraphviz as pgv
from IPython.display import display, Image

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
        nodeset_str = "["
        for vs in nodeset.vs_list:
            nodeset_str += vs.name + "," + str(vs.version) + "\n"
        # Trim the trailing comma
        if len(nodeset.vs_list) > 0:
            nodeset_str = nodeset_str[:-1]
        nodeset_str += "]"
        nodeset_dict[nodeset] = nodeset_str
        display_graph.add_node(nodeset_str, height=1, fontsize=8)

    # Add string representation of OEs.
    for oe in graph.operation_events:
        display_graph.add_edge(nodeset_dict[oe.src], nodeset_dict[oe.dst], label="cell " + str(oe.cell_num + 1),fontsize=8)

    # Add inter-cell dependencies.
    for dst in graph.output_nodesets:
        for src in graph.input_nodesets:
            if set(dst.vs_list).intersection(set(src.vs_list)):
                display_graph.add_edge(nodeset_dict[dst], nodeset_dict[src], style='dashed')

    # Draw the graph.
    #pos = nx.spring_layout(display_graph)
    #nx.draw_networkx(display_graph, pos, with_labels = True)
    #nx.draw_networkx_edge_labels(display_graph, pos)
    display_graph.graph['graph'] = {'rankdir':'TD'}
    display_graph.graph['node'] = {'shape':'circle'}
    display_graph.graph['edges'] = {'arrowsize':'4.0'}

    A = to_agraph(display_graph)
    A.graph_attr["rankdir"] = 'LR'
    A.layout('dot')
    A.draw('abcd.png')
    display(Image(filename='abcd.png'))

    #for oe in graph.operation_events:
    #    print("Operation event ", oe.cell_num, oe.cell_runtime, ":---------------------")
    #    print("Input variable snapshots:---------")
    #    for vs in oe.src.vs_list:
    #        print(vs.name, vs.version, vs.size)
    #    print("Output variable snapshots:---------")
    #    for vs in oe.dst.vs_list:
    #        print(vs.name, vs.version, vs.size)
