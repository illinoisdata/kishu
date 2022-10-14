#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import json
from typing import List, Dict
from elastic.core.graph.graph import DependencyGraph

KEY_DEPENDENCY_GRAPH = "dependencyGraph"
KEY_VARIABLE_VERSION = "variableVersion"

class MigrationMetadata:
    def __init__(self):
        self.dependency_graph = None
        self.variable_version = None

    def with_dependency_graph(self, graph: DependencyGraph):
        self.dependency_graph = graph
        return self

    def get_dependency_graph(self):
        return self.dependency_graph

    def with_variable_version(self, variable_version: Dict):
        self.variable_version = variable_version
        return self

    def get_variable_version(self):
        return self.variable_version

    def to_json_str(self) -> str:
        return json.dumps({
            "dependencyGraph": self.dependency_graph,
            "variableVersion": self.variable_version
        })


    @staticmethod
    def from_json(kv: Dict):
        return MigrationMetadata().with_dependency_graph(kv[KEY_DEPENDENCY_GRAPH])\
                                  .with_variable_version(kv[KEY_VARIABLE_VERSION])
