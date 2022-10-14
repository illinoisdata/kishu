#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from typing import List
from elastic.core.graph.edge import Edge
from elastic.core.graph.node_set import NodeSetType


def find_edges_to_recompute(graph) -> List[Edge]:
    # find nodes to recompute, i.e. active nodes that are not migrated
    migrated_nodes = list(set(graph.active_nodes) - set(graph.nodes_to_recompute))
    
    # find all nodesets that generated these variables
    dst_nodesets = set([node.output_nodeset for node in graph.nodes_to_recompute])
    dst_nodesets = list(dst_nodesets)

    edges_to_recompute = set()
    
    # search for all necessary upstream nodesets via BFS
    queue = dst_nodesets
    while queue:
        nodeset = queue.pop(0)
        input_nodeset, oe = nodeset.edge.src, nodeset.edge.oe

        edges_to_recompute.add(nodeset.edge)
        if input_nodeset.type == NodeSetType.DUMMY:
            continue
        
        for node in input_nodeset.nodes:
            if node in migrated_nodes:
                continue
            output_nodeset = node.output_nodeset
            if output_nodeset.edge in edges_to_recompute:
                continue
            queue.append(output_nodeset)
    
    return list(edges_to_recompute)
        