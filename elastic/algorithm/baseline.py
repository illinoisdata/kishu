#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import random
import math
from typing import List
from elastic.algorithm.selector import Selector
from elastic.core.graph.variable_snapshot import VariableSnapshot


class MigrateAllBaseline(Selector):
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_nodes(self):
        """
        Returns:
            List[VariableSnapshot]: the list of all active nodes are returned so that they are all migrated
        """
        return self.active_vss


class RecomputeAllBaseline(Selector):
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_nodes(self):
        """
        Returns:
            List[VariableSnapshot]: the empty list is returned so that no active nodes are migrated and all recomputed
        """
        return []


class RandomBaseline(Selector):
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_nodes(self):
        """
        Returns:
            List[VariableSnapshot]: a random subset of active nodes is returned
        """
        # NOTE: when this selector is used, the caller should fix a particular seed, for example in the 
        #   automation script for benchmarking
        return random.sample(self.active_vss, math.floor(len(self.active_vss) / 2))
