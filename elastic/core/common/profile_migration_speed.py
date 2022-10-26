#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

def profile_migration_speed(filename: str) -> float:
    """
        TODO: Profiles the I/O speed to directory containing 'filename'.
        The migration speed is the sum of read and write speed (since we are writing the state to disk, then
        reading from disk to restore the notebook). The function should ideally be fast (<1 sec).
        Args:
            filename: Location/filename to profile.
    """
    return 100000  # Hard-coded
