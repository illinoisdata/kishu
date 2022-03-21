#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import datetime

from core.event import DataEvent

data_events = []
operation_events = []
operation_event_lookup = {}

class DataContainer:
    def __init__(self, obj, prevOpEvent):
        try:
            if obj._is_illinois_data_container():
                self.__dict__['_illinoisBaseObj'] = obj._illinoisBaseObj
                self.__dict__['_illinoisPrevOpEvent'] = obj._illinoisPrevOpEvent
                return
        except:
            pass
        self.__dict__['_illinoisBaseObj'] = obj
        self.__dict__['_illinoisPrevOpEvent'] = prevOpEvent
            
    def __iter__(self):
        for x in self._illinoisBaseObj.__iter__():
            self.createDataEvent()
            yield DataContainer(x, self._illinoisPrevOpEvent)
            
    def __call__(self, *args, **kwargs):
        rtv = self._illinoisBaseObject.__call__(*args, **kwargs)
        
        self.createDataEvent()
        return rtv
            
    def __len__(self):
        rtv = self._illinoisBaseObj.__len__()
        
        self.createDataEvent()
        return rtv
    
    def __int__(self):
        self.createDataEvent()
        return int(self._illinoisBaseObj)
    
    def __index__(self):
        return self.__int__()
    
    def __bool__(self):
        rtv = self._illinoisBaseObject.__bool__()
        
        self.createDataEvent()
        return rtv
    
    def __neg__(self):
        self.createDataEvent()
        return self._illinoisBaseObj.__neg__()
    
    def __invert__(self):
        self.createDataEvent()
        return self._illinoisBaseObj.__invert__()
    
    def __pos__(self):
        self.createDataEvent()
        return self._illinoisBaseObj.__pos__()
    
    def __abs__(self):
        self.createDataEvent()
        return self._illinoisBaseObj.__abs__()
    
    def __add__(self, other):
        self.createDataEvent()
        if other.is_data_container():
            other.createDataEvent()
            return self._illinoisBaseObj + other._illinoisBaseObj
        return self._illinoisBaseObj + other
    
    def __sub__(self, other):
        return self.__add__(other.__neg__())
    
    def __mul__(self, other):
        self.createDataEvent()
        if other.is_data_container():
            other.createDataEvent()
            return self._illinoisBaseObj * other._illinoisBaseObj
        return self._illinoisBaseObj * other
    
    def __rmul__(self, other):
        return other.__mul__(self)
    
    def __truediv__(self, other):
        self.createDataEvent()
        if other.is_data_container():
            other.createDataEvent()
            return self._illinoisBaseObj / other._illinoisBaseObj
        return self._illinoisBaseObj / other
    
    def __rtruediv__(self, other):
        self.createDataEvent()
        if other.is_data_container():
            other.createDataEvent()
            return other._illinoisBaseObj / self._illinoisBaseObj
        return other / self._illinoisBaseObj
    
    def __floordiv__(self, other):
        self.createDataEvent()
        if other.is_data_container():
            other.createDataEvent()
            return self._illinoisBaseObj // other._illinoisBaseObj
        return self._illinoisBaseObj // other
    
    def __rfloordiv__(self, other):
        self.createDataEvent()
        if other.is_data_container():
            other.createDataEvent()
            return other._illinoisBaseObj // self._illinoisBaseObj
        return other // self._illinoisBaseObj
    
    def __contains__(self, key):
        rtv = key in self._illinoisBaseObj
        
        self.createDataEvent()
        return rtv
    
    def __getitem__(self, key):
        rtv = self._illinoisBaseObj[key]
        
        self.createDataEvent()
        return rtv
    
    def __setitem__(self, key, value):
        self._illinoisBaseObj.__setitem__(key, value)
        
        self.createDataEvent()
    
    def __delitem__(self, key):
        self._illinoisBaseObj.__delitem__(key)
        
        self.createDataEvent()
    
    def __str__(self):
        rtv = self._illinoisBaseObj.__str__()
    
        self.createDataEvent()
        return rtv
    
    def __repr__(self):
        rtv = self._illinoisBaseObj.__repr__()
        
        self.createDataEvent()
        return rtv
    
    def __setattr__(self, k, v):
        if k in self.__dict__:
            self.__dict__[k] = v
        else:
            setattr(self._illinoisBaseObj, k, v)

        self.createDataEvent()

    def __getattr__(self, k):
        rtv = getattr(self._illinoisBaseObj, k)
        
        self.createDataEvent()
        return rtv
    
    @property
    def __class__(self):
        return self._illinoisBaseObj.__class__
    
    def _is_illinois_data_container(self):
        return True

    def get_base_id(self):
        return id(self._illinoisBaseObj)
    
    def get_base_type(self):
        return type(self._illinoisBaseObj)
    
    def createDataEvent(self):
        data_events.append(DataEvent(self, 
                                     self.get_base_id(), 
                                     self.get_base_type(),
                                     datetime.datetime.now(),
                                     self._illinoisPrevOpEvent))