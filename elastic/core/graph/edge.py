#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.event import OperationEvent
from core.graph.node_set import NodeSet

class Edge:
    def __init__(self, oe: OperationEvent, duration, src: NodeSet, dst: NodeSet) -> None:
        self.oe = oe
        self.duration = duration
        self.src = src
        self.dst = dst
        
    def get_duration(self):
        return self.duration

    def __str__(self):
        return self.__repl__()

    def __repr__(self):
        return self.__repl__()

    def __repl__(self):
        return "Edge details:- \n" + \
                "Operation Event - " + str(self.oe) + "\n" + \
                "Duration - " + str(self.duration) + "\n" + \
                "Source - " + str(self.src) + "\n" + \
                "Destination - " + str(self.dst) + "\n"
