#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import json
from typing import List, Dict
from elastic.core.graph.graph import DependencyGraph

KEY_DEPENDENCY_GRAPH = "dependencyGraph"
KEY_VARIABLES = "variables"
KEY_VSS_TO_MIGRATE = "vss_to_migrate"
KEY_VSS_TO_RECOMPUTE = "vss_to_recompute"
KEY_OES_TO_RECOMPUTE = "oes_to_recompute"

class MigrationMetadata:
    def __init__(self):
        self.dependency_graph = None
        self.variables = None
        self.vss_to_migrate = None
        self.vss_to_recompute = None
        self.oes_to_recompute = None

    def with_dependency_graph(self, graph: DependencyGraph):
        self.dependency_graph = graph
        return self

    def get_dependency_graph(self):
        return self.dependency_graph

    def with_variables(self, variables: Dict):
        self.variables = variables
        return self

    def get_variables(self):
        return self.variables

    def with_vss_to_migrate(self, vss_to_migrate: set):
        self.vss_to_migrate = vss_to_migrate
        return self

    def get_vss_to_migrate(self):
        return self.vss_to_migrate

    def with_vss_to_recompute(self, vss_to_recompute: set):
        self.vss_to_recompute = vss_to_recompute
        return self

    def get_vss_to_recompute(self):
        return self.vss_to_recompute

    def with_oes_to_recompute(self, oes_to_recompute: set):
        self.oes_to_recompute = oes_to_recompute
        return self

    def get_oes_to_recompute(self):
        return self.oes_to_recompute

    def to_json_str(self) -> str:
        return json.dumps({
            KEY_DEPENDENCY_GRAPH: self.dependency_graph,
            KEY_VARIABLES: self.variables,
            KEY_VSS_TO_MIGRATE: self.vss_to_migrate,
            KEY_VSS_TO_RECOMPUTE: self.vss_to_recompute,
            KEY_OES_TO_RECOMPUTE: self.oes_to_recompute
        })


    @staticmethod
    def from_json(kv: Dict):
        return MigrationMetadata().with_dependency_graph(kv[KEY_DEPENDENCY_GRAPH])\
                                  .with_imported_modules(kv[KEY_IMPORTED_MODULES])\
                                  .with_variables(kv[KEY_VARIABLES])\
                                  .with_vss_to_migrate(kv[KEY_VSS_TO_MIGRATE])\
                                  .with_vss_to_recompute(kv[KEY_VSS_TO_RECOMPUTE])\
                                  .with_oes_to_recompute(kv[KEY_OES_TO_RECOMPUTE])
