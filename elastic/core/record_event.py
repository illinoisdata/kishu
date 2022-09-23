#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import datetime
import inspect
import uuid

from core.container import DataContainer, OperationContainer
from core.event import OperationEvent, data_events, data_containers, data_container_version, operation_events, \
    operation_event_lookup

def ClearEvent():
    data_events.clear()
    data_containers.clear()
    operation_events.clear()
    operation_event_lookup.clear()

def RecordEvent(func):
    def func_wrapper(*args, **kwargs):
        exec_uuid = len(operation_events)
        ##exec_uuid = uuid.uuid4()
        print(*args)
        
        start_time = datetime.datetime.now()
        rtv = func(*args, **kwargs)
        end_time = datetime.datetime.now()
        
        related_data_events = [de for de in data_events if (de.event_time >= start_time 
                                                                              and de.event_time <= end_time)]
        
        oe = OperationEvent(exec_uuid=exec_uuid,
                            start=start_time, 
                            end=end_time, 
                            duration=(end_time - start_time).total_seconds(),
                            cell_func_name=func.__name__,
                            cell_func_code=inspect.getsource(func),
                            related_data_events=related_data_events)
        operation_events.append(oe)
        operation_event_lookup[exec_uuid] = oe

        if rtv is not None and type(rtv) is OperationContainer:
            for key, item in rtv.items.items():
                data_container_version[key] += 1
                if type(item) is DataContainer:
                    container = DataContainer(key, data_container_version[key], item.get_item(), oe)
                else:
                    container = DataContainer(key, data_container_version[key], item, oe)
                print("container created for variable ", key)
                data_containers.append(container)
                oe.output_data_containers.append(container)
            return tuple(oe.output_data_containers)
        else:
            return rtv

    return func_wrapper