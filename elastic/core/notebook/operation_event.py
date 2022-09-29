#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

# An OperationEvent is an instance of cell execution.
class OperationEvent:
    def __init__(self, exec_uuid, start, end, duration,
                 cell_func_name,
                 cell_func_code,
                 input_variable_snapshots):
        self.exec_uuid = exec_uuid
        self.start = start
        self.end = end
        self.duration = duration
        self.cell_func_name = cell_func_name
        self.cell_func_code = cell_func_code
        self.input_variable_snapshots = input_variable_snapshots
        self.output_variable_snapshots = []

    def __str__(self):
        return self.__repl__()

    def __repl__(self):
        return "Operation with name {} and id {} started at {} and ended at {}," \
               " {} s elapsed, {} input variable snapshots".format(self.cell_func_name,
                                                                   self.exec_uuid,
                                                                   self.start,
                                                                   self.end,
                                                                   self.duration,
                                                                   len(self.input_variable_snapshots))

    def get_exec_id(self):
        return self.exec_uuid
