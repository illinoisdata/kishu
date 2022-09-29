#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from collections import defaultdict

# List for determining variable snapshot usage in operation events. Cleared at the end of each cell run.
variable_snapshot_accesses = []

# Map from variable name to variable version.
variable_version = defaultdict(int)

# List of variable snapshots (versioned variables).
variable_snapshots = []

# List of operation events (cell executions).
operation_events = []


def reset_notebook_state():
    variable_snapshot_accesses.clear()
    variable_version.clear()
    variable_snapshots.clear()
    operation_events.clear()
