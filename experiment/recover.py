#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import json

from elastic.common.migration_metadata import MigrationMetadata
from elastic.io.external_storage import ExternalStorage

from experiment.migrate import METADATA_PATH, OBJECT_PATH_PREFIX

def resume(storage: ExternalStorage):
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
    metadata = json.loads(storage.read_all(METADATA_PATH))
    metadata = MigrationMetadata.from_json(metadata)
