#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from typing import List
from core.event import OperationEvent
from core.graph.graph import DependencyGraph
from core.graph.node import Node
from core.graph.node_set import NodeSet, NodeSetType


def find_path(graph: DependencyGraph,
              migrated_nodes: List[Node],
              operation_events) -> List[OperationEvent]:
    # find nodes to recompute, i.e. active nodes that are not migrated
    recomputed_nodes = set(graph.active_nodes.values()) - set(migrated_nodes)
    recomputed_nodes = list(recomputed_nodes)
    
    # find all nodesets that generated these variables
    source_nodesets = set([node.output_nodeset for node in recomputed_nodes])
    source_nodesets = list(source_nodesets)
    
    # an operation needs to be rerun if its mask value is True
    recom_mask = [False for _ in operation_events]
    
    # search for all necessary upstream nodesets
    queue = source_nodesets
    while queue:
        nodeset = queue.pop(0)
        input_nodeset, oe = nodeset.edge.src, nodeset.edge.oe
        
        recom_mask[oe.get_exec_id()] = True
        if input_nodeset.type == NodeSetType.DUMMY:
            continue
        
        for node in input_nodeset.nodes:
            output_nodeset = node.output_nodeset
            if recom_mask[output_nodeset.edge.oe.get_exec_id()]:
                continue
            queue.append(output_nodeset)
    
    result = []
    for oe in operation_events:
        if recom_mask[oe.get_exec_id()]:
            result.append(oe)
    
    return result
        