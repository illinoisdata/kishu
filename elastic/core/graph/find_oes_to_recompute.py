#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from typing import List
from elastic.core.graph.operation_event import OperationEvent
from elastic.core.graph.node_set import NodeSetType


def find_oes_to_recompute(vss_to_migrate: set, vss_to_recompute: set) -> set:
    """
        Finds the OEs to recompute given the VSs to migrate and recompute via BFS.
        Args:
            vss_to_migrate (set): VSs to migrate.
            vss_to_recompute (set): VSs to recompute.
    """

    # find all nodesets that generated the VSs to recompute.
    dst_nodesets = set([vs.output_nodeset for vs in vss_to_recompute])
    dst_nodesets = list(dst_nodesets)

    oes_to_recompute = set()
    
    # search for all necessary upstream nodesets via BFS.
    queue = dst_nodesets
    while queue:
        nodeset = queue.pop(0)
        input_nodeset = nodeset.operation_event.src

        oes_to_recompute.add(nodeset.operation_event)
        if input_nodeset.type == NodeSetType.DUMMY:
            continue
        
        for vs in input_nodeset.vs_list:
            if vs in vss_to_migrate:
                continue
            output_nodeset = vs.output_nodeset
            if output_nodeset.operation_event in oes_to_recompute:
                continue
            queue.append(output_nodeset)
    
    return oes_to_recompute
