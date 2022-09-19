from core.graph.edge import Edge
from core.graph.graph import DependencyGraph
from core.event import OperationEvent, data_events, data_containers, operation_events, operation_event_lookup
from core.graph.node_set import NodeSet
from core.graph.node_set import NodeSetType

class GraphConstruction:

    def __init__(self):
        self.graph = DependencyGraph()

    def create_edges(self):
        print("Creating an edge for each Operation Event in the Dependency Graph")
        
        for i in operation_events:

            # Find input nodes corresponding to this OE
            srcNodes = self.get_source_nodes(i)
            dstNodes = self.get_destination_nodes(i)
            
            src = NodeSet(srcNodes,NodeSetType.INPUT)
            if srcNodes == None or len(srcNodes) == 0:
                src.type = NodeSetType.DUMMY
            dst = NodeSet(dstNodes, NodeSetType.OUTPUT)

            self.graph.add_edge(src,dst,i)
        
    def get_source_nodes(self,oe):
        srcNodes = []
        # Find source nodes here
        # I'll have a dictionary with data containers base id to node mapping
        return srcNodes

    def get_destination_nodes(self,oe):
        dstNodes = []
        #  Find destination nodes here
        # I'll have a dictionary with O.E exec_uuid to node mapping
        return dstNodes