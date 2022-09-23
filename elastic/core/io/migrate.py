#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import pickle
from pathlib import Path
from typing import List
from core.common.migration_metadata import MigrationMetadata

from core.io.external_storage import ExternalStorage

METADATA_PATH = "../../experiment/metadata.json"
CODE_PATH = "./code.py"
OBJECT_PATH_PREFIX = "./obj_"

def migrate(nodes_to_migrate: List,
            edges_to_migrate: List,
            notebook_name):
    """
    (1) Iterate over all objects in `objects_to_migrate`. For each object
        (1a) Pickle the object
        (1b) Write to external storage
    (2) Write code and metadata to external storage

    Args:
        objects_to_migrate (List):
            a list of python objects to migrate
        oe_to_migrate (str):
            a string containing all the code needed for recomputation
        metadata (MigrationMetadata):
            a JSON structure containing migration metadata
        external_storage (ExternalStorage):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
        context_items (List):
            a list of all objects' name to value mapping in global/local context of caller
    """

    # Convert to dictionary for migration
    data_container_dict = {}
    for node in nodes_to_migrate:
        data_container_dict[node.var.name] = node.dc.get_item()

    recomputation_code = []

    # Iterate over cells to recompute
    for edge in edges_to_migrate:
        # Find input variables of cell code; these variables should be initialized prior to cell code execution.
        for node in edge.src.nodes:
            if node.var.name in data_container_dict:
                recomputation_code.append("{} = data_container_dict[\"{}\"]".format(node.var.name, node.var.name))

        # Find output variables of cell; assign values to them after executing cell
        dst_names = []
        for node in edge.dst.nodes:
            dst_names.append(node.var.name)

        # Add cell code (with @recordevent trimmed) to recomputation code
        trimmed_code = edge.oe.cell_func_code.split(' ', 1)[1].split(' return ')[0]
        trimmed_code = 'def ' + trimmed_code
        trimmed_code += ' return ' + ", ".join(dst_names)
        recomputation_code.append(trimmed_code)

        # Assign values to output variables after executing cell
        recomputation_code.append(", ".join(dst_names) + " = " + edge.oe.cell_func_name + "()")

        file = open(notebook_name, 'wb')
        pickle.dump((data_container_dict, recomputation_code), file)

    return recomputation_code

        # obj_pickled = pickle.dumps(obj)
        # obj_path = "{}{}".format(OBJECT_PATH_PREFIX, id(obj))
        
    #     # FIXME: might be optimizable using batch writes (especially for remote storage using req/resp)
    #     storage.write_all(Path(obj_path), obj_pickled)
    #
    #     # construct a mapping from object path to a list of all names that reference that object
    #     # so that we know what variable name to use at resume time
    #     objects_migrated[obj_path] = [ k for k,v in context_items if v is obj ]
    #
    # # assume that the list of ids of objects to migrate is already part of the metadata
    #
    # metadata_json = MigrationMetadata().with_objects_migrated(objects_migrated)\
    #                                    .with_recompute_code(code_to_migrate)\
    #                                    .to_json_str()
    # metadata_json = str.encode(metadata_json)
    # storage.write_all(Path(METADATA_PATH), metadata_json)
