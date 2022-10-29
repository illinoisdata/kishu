#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import random
import math
from typing import List

import numpy as np

from elastic.algorithm.selector import Selector
from elastic.core.graph.variable_snapshot import VariableSnapshot


class MigrateAllBaseline(Selector):
    """
        Migrates all active VSs.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_vss(self) -> set:
        vss_to_migrate = set()
        for vs in self.active_vss:
            if vs.size < np.inf:
                vss_to_migrate.add(vs)
        return vss_to_migrate


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
        NOTE: when this selector is used, the caller should fix a particular seed.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_vss(self) -> set:
        vss_to_migrate = set()
        for vs in self.active_vss:
            if vs.size < np.inf and random.random() < 0.5:
                vss_to_migrate.add(vs)
        return vss_to_migrate
