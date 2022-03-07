#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

KEY_OBJECTS_MIGRATED = "objectsMigrated"
KEY_RECOMPUTE_CODE = "recomputeCode"

class MigrationMetadata:
    def __init__(self):
        pass


    def with_objects_migrated(self, objects: dict):
        self.objects_migrated = objects
        return self


    def get_objects_migrated(self):
        return self.objects_migrated


    def with_recompute_code(self, recompute: list):
        self.recomputeCode = recompute


    def get_recompute_code(self):
        return self.recomputeCode


    def to_json(self):
        return {
            "objectsMigrated": self.objects_migrated,
            "recomputeCode": self.recomputeCode
        }


    @staticmethod
    def from_json(kv: dict):
        return MigrationMetadata().with_objects_migrated(kv[KEY_OBJECTS_MIGRATED])\
                                  .with_recompute_code(KEY_RECOMPUTE_CODE)
