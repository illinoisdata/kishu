#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import datetime

import sys
from elastic.core.globals import variable_snapshot_accesses


# A VariableSnapshot is an instance/version of a variable.
class VariableSnapshot:
    def __init__(self, varname, version, obj, prevOpEvent, migrate_flag = True):
        try:
            if obj._is_illinois_variable_snapshot():
                self.__dict__['_varname'] = varname
                self.__dict__['_version'] = version
                self.__dict__['_illinoisBaseObj'] = obj._illinoisBaseObj
                self.__dict__['_illinoisPrevOpEvent'] = obj._illinoisPrevOpEvent
                self.__dict__['_migrate'] = migrate_flag
                return
        except:
            pass
        self.__dict__['_varname'] = varname
        self.__dict__['_version'] = version
        self.__dict__['_illinoisBaseObj'] = obj
        self.__dict__['_illinoisPrevOpEvent'] = prevOpEvent
        self.__dict__['_migrate'] = migrate_flag
            
    def __iter__(self):
        rtv = self.__dict__['_illinoisBaseObj'].__iter__() 
        
        self.create_access()
        return rtv
            
    def __next__(self):
        rtv = self._illinoisBaseObject.__next__()
        
        self.create_access()
        return rtv
            
    def __call__(self, *args, **kwargs):
        rtv = self._illinoisBaseObject.__call__(*args, **kwargs)
        
        self.create_access()
        return rtv
            
    def __len__(self):
        rtv = self._illinoisBaseObj.__len__()
        
        self.create_access()
        return rtv
    
    def __int__(self):
        self.create_access()
        return int(self._illinoisBaseObj)
    
    def __index__(self):
        return self.__int__()
    
    def __bool__(self):
        rtv = self._illinoisBaseObject.__bool__()
        
        self.create_access()
        return rtv
    
    def __neg__(self):
        self.create_access()
        return self._illinoisBaseObj.__neg__()
    
    def __invert__(self):
        self.create_access()
        return self._illinoisBaseObj.__invert__()
    
    def __pos__(self):
        self.create_access()
        return self._illinoisBaseObj.__pos__()
    
    def __abs__(self):
        self.create_access()
        return self._illinoisBaseObj.__abs__()
    
    def __add__(self, other):
        self.create_access()
        if other.is_variable_snapshot():
            other.create_access()
            return self._illinoisBaseObj + other._illinoisBaseObj
        return self._illinoisBaseObj + other
    
    def __sub__(self, other):
        return self.__add__(other.__neg__())
    
    def __mul__(self, other):
        self.create_access()
        if other.is_variable_snapshot():
            other.create_access()
            return self._illinoisBaseObj * other._illinoisBaseObj
        return self._illinoisBaseObj * other
    
    def __rmul__(self, other):
        return other.__mul__(self)
    
    def __truediv__(self, other):
        self.create_access()
        if other.is_variable_snapshot():
            other.create_access()
            return self._illinoisBaseObj / other._illinoisBaseObj
        return self._illinoisBaseObj / other
    
    def __rtruediv__(self, other):
        self.create_access()
        if other.is_variable_snapshot():
            other.create_access()
            return other._illinoisBaseObj / self._illinoisBaseObj
        return other / self._illinoisBaseObj
    
    def __floordiv__(self, other):
        self.create_access()
        if other.is_variable_snapshot():
            other.create_access()
            return self._illinoisBaseObj // other._illinoisBaseObj
        return self._illinoisBaseObj // other
    
    def __rfloordiv__(self, other):
        self.create_access()
        if other.is_variable_snapshot():
            other.create_access()
            return other._illinoisBaseObj // self._illinoisBaseObj
        return other // self._illinoisBaseObj
    
    def __contains__(self, key):
        rtv = key in self._illinoisBaseObj
        
        self.create_access()
        return rtv
    
    def __getitem__(self, key):
        rtv = self._illinoisBaseObj[key]
        
        self.create_access()
        return rtv
    
    def __setitem__(self, key, value):
        self._illinoisBaseObj.__setitem__(key, value)
        
        self.create_access()
    
    def __delitem__(self, key):
        self._illinoisBaseObj.__delitem__(key)
        
        self.create_access()
    
    def __str__(self):
        rtv = self._illinoisBaseObj.__str__()
    
        self.create_access()
        return rtv
    
    def __repr__(self):
        rtv = self._illinoisBaseObj.__repr__()
        
        self.create_access()
        return rtv
    
    def __setattr__(self, k, v):
        if k in self.__dict__:
            self.__dict__[k] = v
        else:
            setattr(self._illinoisBaseObj, k, v)

        self.create_access()

    def __getattr__(self, k):
        rtv = getattr(self._illinoisBaseObj, k)
        
        self.create_access()
        return rtv
    
    # for pickling
    def __reduce__(self):
        print("Pickling", self.get_name())
        if self._illinoisBaseObj.__class__.__module__ == 'builtins': # different python versions might have different module names
            return self.__class__, (self._illinoisBaseObj,)
        else:
            return self._illinoisBaseObj.__reduce__()

    # def __reduce_ex__(self, k):
    #     print("Pickling", self.get_name())
    #     if self._illinoisBaseObj.__class__.__module__ == 'builtins': # different python versions might have different module names
    #         return self.__class__, (self._illinoisBaseObj,)
    #     else:
    #         return self._illinoisBaseObj.__reduce_ex__(k)
    
    @property
    def __class__(self):
        return self._illinoisBaseObj.__class__
    
    def _is_illinois_variable_snapshot(self):
        return True

    def get_item(self):
        return self._illinoisBaseObj

    def set_item(self, item):
        self.__dict__['_illinoisBaseObj'] = item

    def clear_item(self):
        self.__dict__['_illinoisBaseObj'] = EmptyObject()

    def get_name(self):
        return self._varname

    def get_version(self):
        return self._version

    def get_base_id(self):
        return id(self._illinoisBaseObj)
    
    def get_base_type(self):
        return type(self._illinoisBaseObj)

    def get_size(self):
        return sys.getsizeof(self._illinoisBaseObj)

    def get_prev_oe(self):
        return self._illinoisPrevOpEvent
    
    def get_migrate_flag(self):
        return self._migrate

    def __repl__(self):
        return "VariableSnapshot with base ID {} and type {}," \
               " previous operation event was {}".format(self.get_base_id,
                                                         self.get_base_type,
                                                         type(self._illinoisBaseObj))

    def create_access(self):
        variable_snapshot_accesses.append(self)


# A set of output variable snapshots from an operation event.
class VariableSnapshotSet:
    def __init__(self, variable_snapshots):
        self.variable_snapshots = variable_snapshots


# For pickling; pickle does not work with Nonetype.
class EmptyObject:
    def __init__(self):
        pass

