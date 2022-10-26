#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import sys


def profile_variable_size(x) -> int:
    """
        Profiles the size of variable x. Notably, this should recursively find the size of lists, sets and dictionaries.
        Args:
            x: The variable to profile.
    """

    """
    TODO: replace sys.getsizeof with a more accurate estimation function.
    sys.getsizeof notably does not work well with nested structures (i.e. lists, dictionaries).
    """
    return sys.getsizeof(x)
