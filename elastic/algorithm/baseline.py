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
    """
        Migrates all active VSs.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_vss(self) -> set:
        return set(self.active_vss)


class RecomputeAllBaseline(Selector):
    """
        Recomputes all active VSs.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_vss(self) -> set:
        return set()


class RandomBaseline(Selector):
    """
        Randomly selects some active VSs to migrate according to a Bernoulli process with p = 0.5.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_vss(self) -> set:
        # NOTE: when this selector is used, the caller should fix a particular seed.
        return random.sample(self.active_vss, math.floor(len(self.active_vss) / 2))
