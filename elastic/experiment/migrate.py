#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import pickle
from pathlib import Path
from typing import List
from core.common.migration_metadata import MigrationMetadata

from core.io.external_storage import ExternalStorage

METADATA_PATH = "./metadata.json"
CODE_PATH = "./code.py"
OBJECT_PATH_PREFIX = "./obj_"

def migrate(objects_to_migrate: List,
            code_to_migrate: str, 
            storage: ExternalStorage,
            context_items: List):
    """
    (1) Iterate over all objects in `objects_to_migrate`. For each object
        (1a) Pickle the object
        (1b) Write to external storage
    (2) Write code and metadata to external storage

    Args:
        objects_to_migrate (List):
            a list of python objects to migrate
        code_to_migrate (str):
            a string containing all the code needed for recomputation
        metadata (MigrationMetadata):
            a JSON structure containing migration metadata
        external_storage (ExternalStorage):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
        context_items (List):
            a list of all objects' name to value mapping in global/local context of caller
    """
    objects_migrated = {}
    
    for obj in objects_to_migrate:
        obj_pickled = pickle.dumps(obj)
        obj_path = "{}{}".format(OBJECT_PATH_PREFIX, id(obj))
        
        # FIXME: might be optimizable using batch writes (especially for remote storage using req/resp)
        storage.write_all(Path(obj_path), obj_pickled)
        
        # construct a mapping from object path to a list of all names that reference that object
        # so that we know what variable name to use at resume time
        objects_migrated[obj_path] = [ k for k,v in context_items if v is obj ]

    # assume that the list of ids of objects to migrate is already part of the metadata
    
    metadata_json = MigrationMetadata().with_objects_migrated(objects_migrated)\
                                       .with_recompute_code(code_to_migrate)\
                                       .to_json_str()
    metadata_json = str.encode(metadata_json)
    storage.write_all(Path(METADATA_PATH), metadata_json)
