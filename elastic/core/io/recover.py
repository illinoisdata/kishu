#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import pickle
from typing import Dict

def resume(storage: str,
           global_state: Dict):
    """
    (1) Busy waits for the file at `migration_metadata_path` in `storage` to appear
    (2) Once the metadata file appears, read the metadata content
        (2a) Recover a list of objects / operation events according to the metadata, 
             which should contain a list of pairs <path, name>.
        (2b) For each object / oe in the list, unpickle the corresponding file in storage
        (2c) Start recomputation (if needed) as instructed in the metadata.

    Args:
        storage (ExternalStorage):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
        global_state (Dict):
            a dictionary that contains environment variables and to store recovered states 
            (need to pass in globals() to get environment variables)
    """
    globals().update(global_state)
    file = open(storage, 'rb')
    items = pickle.load(file)
    data_container_dict = items[0]
    recomputation_code = items[1]

    for code in recomputation_code:
        before_exec = locals().copy()
        exec(code)
        for k in set(locals()) - set(before_exec):
            if k != "before_exec":
                diff = {k: locals()[k]}
                globals().update(diff)
                global_state.update(diff)
