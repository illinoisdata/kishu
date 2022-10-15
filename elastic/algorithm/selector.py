#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from typing import List
from elastic.core.graph.variable_snapshot import VariableSnapshot


class Selector:
    """
        The `Selector` class provides interfaces to pick a subset of active nodes to migrate based on
            various heuristics and algorithms.
    """

    def __init__(self, migration_speed_bps=1):
        self.dependency_graph = None
        self.active_vss = None
        self.migration_speed_bps = migration_speed_bps

    def select_nodes(self):
        """
            Classes that inherit from the `Selector` class (such as `Optimizer` and various baselines)
                should override `select_nodes`

            Returns:
                List[VariableSnapshot]: a subset of active nodes selected to migrate based on various heuristics and algorithms
        """
        raise NotImplementedError()
