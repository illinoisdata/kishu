import unittest

import os, sys

import numpy as np

sys.path.insert(0, os.path.abspath(".."))
from algorithm.optimizer_exact import OptimizerExact
from core.graph.graph import DependencyGraph
from core.graph.node import Node
from core.graph.edge import Edge
from core.graph.node_set import NodeSet
from core.notebook.variable_snapshot import VariableSnapshot
from core.notebook.operation_event import OperationEvent

class TestOptimizer(unittest.TestCase):
    def test_init(self):
        ## Nodes
        nodes = []

        np.random.seed(1234567423)
        for i in range(18):
            size = np.random.rand() * 12
            if 6 <= i <= 9:
                size *= 10
            nodes.append(self.get_test_node(str(i), size, 1))

        ## Node sets
        node_sets = []
        for i in range(0, 18, 2):
            node_sets.append(NodeSet([nodes[i], nodes[i + 1]], None))
        node_sets.append(NodeSet([nodes[3], nodes[6]], None))
        node_sets.append(NodeSet([nodes[7], nodes[10]], None))
        node_sets.append(NodeSet([nodes[14], nodes[15]], None))

        ## Graph
        graph = DependencyGraph()
        graph.add_edge(node_sets[0], node_sets[1], self.get_oe(np.random.rand() * 2))
        graph.add_edge(node_sets[2], node_sets[3], self.get_oe(np.random.rand() * 2))
        graph.add_edge(node_sets[4], node_sets[5], self.get_oe(np.random.rand() * 2))
        graph.add_edge(node_sets[9], node_sets[6], self.get_oe(np.random.rand() * 2))
        graph.add_edge(node_sets[10], node_sets[7], self.get_oe(np.random.rand() * 2))
        graph.add_edge(node_sets[11], node_sets[8], self.get_oe(np.random.rand() * 2))

        graph.active_nodes = nodes

        opt = OptimizerExact(migration_speed_bps=30)
        graph.trim_graph(opt)

        # TODO: think of an illustrating example

    def get_test_node(self, name, size, ver=1):
        a = Node(VariableSnapshot(name, ver, size, None))
        a.size = size
        return a


    def get_oe(self, duration):
        return OperationEvent(1, None, None, duration, "", "", [])
        
if __name__ == '__main__':
    unittest.main()
