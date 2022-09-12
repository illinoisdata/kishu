#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import pickle
from pathlib import Path
from typing import List, Dict
from core.common.migration_metadata import MigrationMetadata

from core.io.external_storage import ExternalStorage

METADATA_PATH = "./metadata.json"
CODE_PATH = "./code.py"
OBJECT_PATH_PREFIX = "./obj_"
OE_PATH_PREFIX = "./oe_"

def migrate(objects_to_migrate: List,
            oe_to_migrate: List,
            storage: ExternalStorage,
            input_mappings: Dict,
            output_mappings: Dict,
            context_items: Dict):
    """
    (1) Iterate over all objects and operation events. For each 
        (1a) Pickle the object / oe
        (1b) Write to external storage
    (2) Write metadata to external storage

    Args:
        objects_to_migrate (List):
            a list of python objects to migrate
        oe_to_migrate (List):
            a list of oe for recomputation
        external_storage (ExternalStorage):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
        input_mappings (Dict):
            mappings from functions to their corresponding input variable names
        output_mappings (Dict):
            mappings from functions to their corresponding output variable names
        context_items (List):
            a list of all objects' name to value mapping in global/local context of caller
    """
    objects_migrated = {}
    for obj_name in objects_to_migrate:
        obj = context_items[obj_name]
        obj_pickled = pickle.dumps(obj)
        obj_path = "{}{}".format(OBJECT_PATH_PREFIX, id(obj))
        # FIXME: might be optimizable using batch writes (especially for remote storage using req/resp)
        storage.write_all(Path(obj_path), obj_pickled)
        objects_migrated[obj_path] = obj_name

    oe_migrated = {}
    for oe_name in oe_to_migrate:
        oe = context_items[oe_name]
        oe_pickled = pickle.dumps(oe)
        oe_path = "{}{}".format(OE_PATH_PREFIX, id(oe))
        storage.write_all(Path(oe_path), oe_pickled)
        oe_migrated[oe_path] = oe_name

    # assume that the list of ids of objects to migrate is already part of the metadata
    metadata_json = MigrationMetadata().with_objects_migrated(objects_migrated)\
                                       .with_recompute_code(oe_migrated)\
                                       .with_input_mappings(input_mappings)\
                                       .with_output_mappings(output_mappings)\
                                       .with_order_list(oe_to_migrate)\
                                       .to_json_str()
    metadata_json = str.encode(metadata_json)
    storage.write_all(Path(METADATA_PATH), metadata_json)
