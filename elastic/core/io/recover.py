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

from core.io.migrate import METADATA_PATH

def resume(storage):
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
    file = open(storage, 'rb')
    items = pickle.load(file)
    data_container_dict = items[0]
    recomputation_code = items[1]
    
    return data_container_dict, recomputation_code
