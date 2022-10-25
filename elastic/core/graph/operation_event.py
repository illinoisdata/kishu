#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from elastic.core.graph.node_set import NodeSet


class OperationEvent:
    """
        An operation event corresponds to a cell execution. A cell executed n times will have n corresponding
        operation events.
    """
    def __init__(self, cell_num: int, cell: str, cell_runtime: float, start_time: float, src: NodeSet, dst: NodeSet):
        """
            Create an operation event from cell execution metrics.
            Args:
                cell_num (int): The nth cell execution of the current session.
                cell (str): Raw cell cell.
                cell_runtime (float): Cell runtime.
                start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                    queued.
                src (Nodeset): Nodeset containing input VSs of the cell execution.
                dst(NodeSet): Nodeset containing output VSs of the cell execution.
        """

        self.cell_num = cell_num
        self.cell = cell
        self.cell_runtime = cell_runtime
        self.start_time = start_time
        self.src = src
        self.dst = dst
