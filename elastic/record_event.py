#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import datetime
import inspect
import uuid

import elastic.container
from elastic.container import DataContainer
from elastic.event import OperationEvent

def RecordEvent(func):
    def func_wrapper(*args, **kwargs):
        exec_uuid = uuid.uuid4()
        
        start_time = datetime.datetime.now()
        rtv = func(*args, **kwargs)
        end_time = datetime.datetime.now()
        
        related_data_events = [de for de in elastic.container.data_events if (de.event_time >= start_time 
                                                                              and de.event_time <= end_time)]
        
        oe = OperationEvent(exec_uuid=exec_uuid, 
                            start=start_time, 
                            end=end_time, 
                            duration=(end_time - start_time), 
                            cell_func_name=func.__name__,
                            cell_func_code=inspect.getsource(func),
                            related_data_events=related_data_events)
        elastic.container.operation_events.append(oe)
        elastic.container.operation_event_lookup[exec_uuid] = oe
        
        return DataContainer(rtv, oe) if rtv is not None else rtv
    return func_wrapper