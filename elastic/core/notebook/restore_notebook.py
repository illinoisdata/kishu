#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
from IPython import get_ipython

from elastic.core.graph.graph import DependencyGraph


# Restores the notebook state.
def restore_notebook(dependency_graph: DependencyGraph, variables, oes_to_recompute, shell):
    for oe in dependency_graph.operation_events:
        if oe in oes_to_recompute:
            print("Rerunning cell", oe.cell_num)
            get_ipython().run_cell(oe.code)
        else:
            for pair in sorted(variables[oe], key=lambda item: item[0].index):
                print("Declaring variable", pair[0].name)
                shell.user_ns[pair[0].name] = pair[1]



