import c_idgraph
from typing import Any


class IDGraph:
    """A class that represents an Id Graph."""

    def __init__(self, obj: Any):
        """Create a new IdGraph object with the underlying cObject.(private access)"""
        # This original, referenced object may change
        self.obj = obj
        # This snapshot is not supposed to change
        self.__cObject = c_idgraph.get_idgraph(obj)
        
    def compare(self, graph: Any) -> bool:
        """
            Compares the IdGraph with another IdGraph.

            :param graph: An IDGraph object to compare self with
            :type graph: IDGraph

            :return: This method returns True if the 2 IDGraphs are the same, False otherwise
            :rtype: boolean
        """
        return c_idgraph.compare_graph(self.__cObject, graph.__cObject)
    
    def get_obj_id(self) -> int:
        return c_idgraph.idgraph_obj_id(self.__cObject)

    def get_json(self) -> str:
        """Get the Json object of the Id Graph."""
        return c_idgraph.idgraph_json(self.__cObject)
    
    def __repr__(self) -> str:
        return self.get_json()

    def __str__(self) -> str:
        """Get the string rep of the Id Graph."""
        return self.get_json()

 