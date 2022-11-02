#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import os, time, random, string


def profile_migration_speed(dirname: str) -> float:
    """
        The migration speed is the sum of read and write speed (since we are writing the state to disk, then
        reading from disk to restore the notebook). The function should ideally be fast (<1 sec).
        Args:
            dirname: Location to profile.
    """
    filecount = 10000
    filesize = 1024 * 1024
    max_time = 0.8
    testing_dir = os.path.join(dirname, "measure_speed")
    os.system("rm -rf {} && mkdir {}".format(testing_dir, testing_dir))
    total_bytes = 0
    test_str = string.ascii_letters
    start_time = time.time()
    for i in range(filecount):
        write_loops = int(filesize * (0.5 + random.random()) / len(test_str))
        out_file = open(os.path.join(testing_dir, str(i)), "w")
        for j in range(write_loops):
            out_file.write(test_str)
        out_file.flush()
        total_bytes = total_bytes + len(test_str) * write_loops
        in_file = open(os.path.join(testing_dir, str(i)), "r")
        data = in_file.read()
        total_bytes = total_bytes + len(data)
        out_file.close()
        in_file.close()
        if time.time() - start_time > max_time:
            break
    end_time = time.time()
    os.system("rm -rf {}".format(testing_dir))
    return total_bytes / (end_time - start_time)
