#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import json
from pathlib import Path
import pickle
from typing import Dict

from core.common.migration_metadata import MigrationMetadata
from core.io.external_storage import ExternalStorage

from experiment.migrate import METADATA_PATH

def resume(storage: ExternalStorage,
           global_context: Dict):
    """
    (1) Busy waits for the file at `migration_metadata_path` in `storage` to appear
    (2) Once the metadata file appears, read the metadata content
        (2a) Recover a list of objects according to the metadata, which should contain
             a list of pairs <path, object_name>.
        (2b) For each object in the list, unpickle the corresponding file in storage
        (2c) Start recomputation (if needed) as instructed in the metadata.

    Args:
        migration_metadata_path (MigrationMetadata):
            path to a JSON file in `storage` containing migration metadata
        storage (ExternalStorage):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
    """
    metadata = json.loads(storage.read_all(Path(METADATA_PATH)))
    metadata = MigrationMetadata.from_json(metadata)
    
    # run the recomputation code to get the state of objects that are not migrated
    # this run can be done using a single cell of the new Python session at destination
    # NOTE: this is only needed when we finish experiments and focus on engineering

    for obj_path, obj_names in metadata.get_objects_migrated().items():
        object_pickled = storage.read_all(Path(obj_path))
        obj = pickle.loads(object_pickled)
        
        # link the reconstructed object to the list of object names
        for name in obj_names:
            global_context[name] = obj
