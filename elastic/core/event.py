#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from collections import defaultdict

data_events = []
data_containers = []
data_container_version = defaultdict(int)
operation_events = []
operation_event_lookup = {}


class DataEvent:
    def __init__(self, container, container_id, base_type, event_time, prev_operation_event):
        self.container = container
        self.container_id = container_id
        self.base_type = base_type
        self.event_time = event_time
        self.prev_operation_event = prev_operation_event

    def get_data_event_id(self):
        return id(self)
        
    def __str__(self):
        return self.__repl__()

    def __repl__(self):
        return "DataContainer with base ID {} and type {} used at {}," \
               " previous operation event was {}".format(self.container_id,
                                                         self.base_type,
                                                         self.event_time,
                                                         self.prev_operation_event)


class OperationEvent:
    def __init__(self, exec_uuid, start, end, duration,
                 cell_func_name,
                 cell_func_code,
                 related_data_events):
        self.exec_uuid = exec_uuid
        self.start = start
        self.end = end
        self.duration = duration
        self.cell_func_name = cell_func_name
        self.cell_func_code = cell_func_code
        self.related_data_events = related_data_events
        self.output_data_containers = []

    def __str__(self):
        return self.__repl__()

    def __repl__(self):
        return "Operation with name {} and id {} started at {} and ended at {}," \
               " {} s elapsed, {} related data events".format(self.cell_func_name,
                                                              self.exec_uuid,
                                                              self.start,
                                                              self.end,
                                                              self.duration,
                                                              len(self.related_data_events))

    def get_exec_id(self):
        return self.exec_uuid