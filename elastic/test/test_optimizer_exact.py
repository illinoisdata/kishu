import unittest

import os, sys

sys.path.insert(0, os.path.abspath(".."))
from elastic.algorithm.optimizer_exact import OptimizerExact
from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.operation_event import OperationEvent
from elastic.core.graph.node_set import NodeSet
from elastic.core.notebook.variable_snapshot import VariableSnapshot
from elastic.core.notebook.operation_event import OperationEvent


class TestOptimizer(unittest.TestCase):
    def test_init(self):
        ## Nodes
        nodes = []
        for i in range(18):
            nodes.append(self.get_test_node(str(i), 1))

        ## Node sets
        node_sets = []
        for i in range(0, 18, 2):
            node_sets.append(NodeSet([nodes[i], nodes[i + 1]], None))
        node_sets.append(NodeSet([nodes[3], nodes[6]], None))
        node_sets.append(NodeSet([nodes[7], nodes[10]], None))
        node_sets.append(NodeSet([nodes[14], nodes[15]], None))

        ## Graph
        graph = DependencyGraph()
        graph.edges.append(OperationEvent(self.get_oe(2), node_sets[0], node_sets[1]))
        graph.edges.append(OperationEvent(self.get_oe(2), node_sets[2], node_sets[3]))
        graph.edges.append(OperationEvent(self.get_oe(2), node_sets[4], node_sets[5]))
        graph.edges.append(OperationEvent(self.get_oe(2), node_sets[9], node_sets[6]))
        graph.edges.append(OperationEvent(self.get_oe(2), node_sets[10], node_sets[7]))
        graph.edges.append(OperationEvent(self.get_oe(2), node_sets[11], node_sets[8]))

        opt = OptimizerExact(migration_speed_bps=1)
        graph.trim_graph(opt)

        # TODO: think of an illustrating example

    def get_test_node(self, name, ver=1):
        return VariableSnapshot(VariableSnapshot(name, ver, None, None))

    def get_oe(self, duration):
        return OperationEvent(1, None, None, duration, "", "", [])


if __name__ == '__main__':
    unittest.main()
