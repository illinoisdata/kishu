#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

KEY_OBJECTS_MIGRATED = "objectsMigrated"
KEY_RECOMPUTE_SEQUENCE = "recomputeSequence"

class MigrationMetadata:
    def __init__(self):
        pass


    def with_objects_migrated(self, objects: list):
        self.objects_migrated = objects
        return self


    def with_recompute_seq(self, recompute: list):
        self.recompute_seq = recompute


    def to_json(self):
        return {
            "objectsMigrated": self.objects_migrated,
            "recomputeSequence": self.recompute_seq
        }


    @staticmethod
    def from_json(kv: dict):
        return MigrationMetadata().with_objects_migrated(kv[KEY_OBJECTS_MIGRATED])\
                                  .with_recompute_seq(KEY_RECOMPUTE_SEQUENCE)
