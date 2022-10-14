#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import datetime
import inspect

from elastic.core.notebook.variable_snapshot import VariableSnapshot, VariableSnapshotSet
from elastic.core.notebook.operation_event import OperationEvent
from elastic.core.globals import variable_snapshots, operation_events, variable_version, variable_snapshot_accesses


# The RecordEvent annotation wraps notebook cell code and generates an OperationEvent with each cell execution.
def RecordEvent(func):
    def func_wrapper(*args, **kwargs):
        exec_uuid = len(operation_events)
        print(*args)
        
        start_time = datetime.datetime.now()
        rtv = func(*args, **kwargs)
        end_time = datetime.datetime.now()
        
        input_variable_snapshots = list(set(variable_snapshot_accesses))
        variable_snapshot_accesses.clear()
        
        oe = OperationEvent(exec_uuid=exec_uuid,
                            start=start_time, 
                            end=end_time, 
                            duration=(end_time - start_time).total_seconds(),
                            cell_func_name=func.__name__,
                            cell_func_code=func.__code__,
                            input_variable_snapshots=input_variable_snapshots)
        operation_events.append(oe)
        # operation_event_lookup[exec_uuid] = oe

        if rtv is not None and type(rtv) is VariableSnapshotSet:
            for key, item in rtv.variable_snapshots.items():
                variable_version[key] += 1
                migrate_flag = False if func.__name__ == "import_libraries" else True
                if type(item) is VariableSnapshot:
                    container = VariableSnapshot(key, variable_version[key], item.get_item(), oe, migrate_flag)
                    item.clear_item()
                else:
                    container = VariableSnapshot(key, variable_version[key], item, oe, migrate_flag)
                print("container created for variable ", key)
                variable_snapshots.append(container)
                oe.output_variable_snapshots.append(container)
            return tuple(oe.output_variable_snapshots)
        else:
            return rtv

    return func_wrapper
