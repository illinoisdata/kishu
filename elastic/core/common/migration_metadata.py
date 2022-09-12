#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import json
from typing import List, Dict

KEY_OBJECTS_MIGRATED = "objectsMigrated"
KEY_RECOMPUTE_CODE = "recomputeCode"
KEY_INPUT_MAPPINGS = "inputMappings"
KEY_OUTPUT_MAPPINGS = "outputMappings"
KEY_ORDER_LIST = "orderList"

class MigrationMetadata:
    def __init__(self):
        pass


    def with_objects_migrated(self, objects: Dict):
        self.objects_migrated = objects
        return self


    def get_objects_migrated(self):
        return self.objects_migrated


    def with_recompute_code(self, recompute: Dict):
        self.recomputeCode = recompute
        return self


    def get_recompute_code(self):
        return self.recomputeCode


    def with_input_mappings(self, input: Dict):
        self.input_mappings = input
        return self


    def get_input_mappings(self):
        return self.input_mappings


    def with_output_mappings(self, ouput: Dict):
        self.output_mappings = ouput
        return self


    def get_output_mappings(self):
        return self.output_mappings


    def with_order_list(self, order: List):
        self.order_list = order
        return self


    def get_order_list(self):
        return self.order_list


    def to_json_str(self) -> str:
        return json.dumps({
            "objectsMigrated": self.objects_migrated,
            "recomputeCode": self.recomputeCode,
            "inputMappings": self.input_mappings,
            "outputMappings": self.output_mappings,
            "orderList": self.order_list
        })


    @staticmethod
    def from_json(kv: Dict):
        return MigrationMetadata().with_objects_migrated(kv[KEY_OBJECTS_MIGRATED])\
                                  .with_recompute_code(kv[KEY_RECOMPUTE_CODE])\
                                  .with_input_mappings(kv[KEY_INPUT_MAPPINGS])\
                                  .with_output_mappings(kv[KEY_OUTPUT_MAPPINGS])\
                                  .with_order_list(kv[KEY_ORDER_LIST])
