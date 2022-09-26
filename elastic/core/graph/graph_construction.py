
from core.graph.graph import DependencyGraph
from core.event import operation_events
from core.graph.node import Node
from core.graph.node_set import NodeSet
from core.graph.node_set import NodeSetType
from core.graph.versioned_var import VersionedVariable


class ConstructGraph:

    def __init__(self) -> None:
        self.graph = DependencyGraph()
        self.versioned_var = {}
        self.construct_graph()

    def create_node(self,dc):

        v_var = None
        if (dc.get_name() in self.versioned_var) and (self.versioned_var[dc.get_name()] == dc.get_name):
            v_var = self.versioned_var[dc.get_name()]
        else:
            v_var = VersionedVariable(dc.get_name(),dc.get_base_id(),dc.get_version())
        node = Node(v_var,dc,dc.get_size())
        self.graph.add_active_node(node)
        return node

    def construct_graph(self):

        for oe in operation_events:
            src_nodes = []
            seen_containers = set()
            for de in oe.related_data_events:
                dc = de.container               # Data Container for this event
                if dc.get_name() not in seen_containers:
                    seen_containers.add(dc.get_name())
                    src_nodes.append(self.create_node(dc))
                    
            src_nodeset = NodeSet(src_nodes,NodeSetType.INPUT)

            dst_nodes = []
            for dc in oe.output_data_containers:
                dst_nodes.append(self.create_node(dc))
            dst_nodeset = NodeSet(dst_nodes,NodeSetType.OUTPUT)

            self.graph.add_edge(src_nodeset,dst_nodeset,oe)
