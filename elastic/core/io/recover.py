#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import json
from pathlib import Path
import pickle
from typing import Dict, List

from core.common.migration_metadata import MigrationMetadata
from core.io.external_storage import ExternalStorage

from core.io.migrate import METADATA_PATH

def getFuncFromString(source_code, name):
    exec(source_code)
    return locals()[name]

def setDictValues(d: Dict, keySet: List, valueSet: List):
    for k, v in zip(keySet, valueSet):
        d[k] = v

def wrapperFunc(func, args):
    return func(*args)

def resume(storage: ExternalStorage,
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
    metadata = json.loads(storage.read_all(Path(METADATA_PATH)))
    metadata = MigrationMetadata.from_json(metadata)
    
    # run the recomputation code to get the state of objects that are not migrated
    # this run can be done using a single cell of the new Python session at destination
    # NOTE: this is only needed when we finish experiments and focus on engineering

    for obj_path, obj_name in metadata.get_objects_migrated().items():
        object_pickled = storage.read_all(Path(obj_path))
        obj = pickle.loads(object_pickled)
        global_state[obj_name] = obj
    for oe_path, oe_name in metadata.get_recompute_code().items():
        oe_pickled = storage.read_all(Path(oe_path))
        source_code = pickle.loads(oe_pickled)
        global_state[oe_name] = getFuncFromString(source_code[source_code.index("def"):], oe_name)

    # recompute based on order list and input/output mappings
    order = metadata.get_order_list()
    input_mappings = metadata.get_input_mappings()
    output_mappings = metadata.get_output_mappings()
    for func in order:
        input_variables = []
        if func in input_mappings:
            input_names = input_mappings[func]
            input_variables = [global_state[k] for k in input_names]
        output_variables = output_mappings[func]
        output_values = wrapperFunc(global_state[func], input_variables)
        setDictValues(global_state, output_variables, output_values)

# def resume(storage):
#     file = open(storage, 'rb')
#     items = pickle.load(file)
#     data_container_dict = items[0]
#     recomputation_code = items[1]
#
#     return data_container_dict, recomputation_code

