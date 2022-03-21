#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import dill
import pickle


def is_picklable(obj):
    return _is_picklable_raw(obj)


def _is_picklable_raw(obj):
    try:
        # dumps can be slow for large objects that can be pickled
        pickle.dumps(obj)
    except Exception:
        return False
    return True


def _is_picklable_dill(obj):
    # compared to _is_picklable_raw, this may be faster
    # however, dill's correctness is worrying because
    #   it currently considers Pandas DataFrame as not
    #   picklable, which is not true
    return dill.pickles(obj)