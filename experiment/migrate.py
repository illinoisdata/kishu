#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import pickle

from elastic.common.migration_metadata import MigrationMetadata
from elastic.io.external_storage import ExternalStorage

METADATA_PATH = "./metadata.json"
OBJECT_PATH_PREFIX = "./obj_"

def migrate(objects_to_migrate, 
            metadata: MigrationMetadata, 
            storage: ExternalStorage):
    """
    (1) Iterate over all objects in `objects_to_migrate`. For each object
        (1a) Pickle the object
        (1b) Write to external storage
    (2) Write metadata to external storage

    Args:
        objects_to_migrate (List):
            a list of python objects to migrate
        metadata (MigrationMetadata):
            a JSON structure containing migration metadata
        external_storage (ExternalStorage):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
    """
    for obj in objects_to_migrate:
        obj_pickled = pickle.dumps(obj)
        # FIXME: might be optimizable using batch writes (especially for remote storage using req/resp)
        storage.write_all(OBJECT_PATH_PREFIX + id(obj), obj_pickled)

    # assume that the list of ids of objects to migrate is already part of the metadata
    storage.write_all(METADATA_PATH, metadata.to_json())
