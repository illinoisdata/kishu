#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.event import OperationEvent
from core.graph.node_set import NodeSet

class Edge:
    def __init__(self, oe: OperationEvent, src: NodeSet, dst: NodeSet) -> None:
        self.oe = oe
        self.src = src
        self.dst = dst
