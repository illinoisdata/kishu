import pickle
from typing import Any, List, Optional

import pandas

import kishu.planning.object_state as object_state
from kishu.planning.visitor import Visitor


def is_pickable(obj) -> bool:
    try:
        if callable(obj):
            return False

        pickle.dumps(obj)
        return True
    except Exception:
        return False


class GraphNode:
    """
    A node in the idgraph. Each node conatins a obj_type, id_obj, check_value_only, and children
    obj_type: The python type of the object for which the node is being built. Default value = type(None)
    id_obj: The id of the object (derived from id(obj)). Default value = 0
    check_value_only: A flag to decide what values to compare for a node:
                        True: compare only value (children)
                        False: compare both value and id
    children: List of children for this particular node

    Note: The check_value_only flag will be set to True only when creating node for objects in the tuple
    returned by invoking __reduce_ex() on an object.
    This is because often the objects returned can be a collection object which is created dynamically
    even though its items might not be. This prevents us
    from getting a False comparison for idgraphs of 2 objects with the same state.
    """

    def __init__(self, obj_type: type = type(None), id_obj: int = 0, check_value_only: bool = False):
        self.obj_type = obj_type
        self.id_obj = id_obj
        self.check_value_only = check_value_only
        self.children: List[Any] = []

    def __eq__(self, other) -> bool:
        return compare_idgraph(self, other)


class idgraph(Visitor):
    def check_visited(
        self, visited: dict, obj_id: int, obj_type: type, include_id: bool, hash_state: None
    ) -> Optional[GraphNode]:
        if obj_id in visited.keys():
            return visited[obj_id]
        else:
            return None

    def visit_primitive(self, obj, hash_state) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    def visit_tuple(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        # Not adding tuple objects to visited dict due to failing test case,
        # possibly due to tuple interning by Python
        for item in obj:
            child = object_state.get_object_state(item, visited, visitor=self, include_id=include_id)

            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_list(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False

        for item in obj:
            child = object_state.get_object_state(item, visited, visitor=self, include_id=include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_set(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), id_obj=id(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        for item in sorted(obj):
            child = object_state.get_object_state(item, visited, visitor=self, include_id=include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_dict(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            # visited[id(obj)] = node
            node.id_obj = id(obj)
            node.check_value_only = False

        for key, value in sorted(obj.items()):
            child = object_state.get_object_state(key, visited, visitor=self, include_id=include_id)
            node.children.append(child)
            child = object_state.get_object_state(value, visited, visitor=self, include_id=include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_byte(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    def visit_type(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        node.children.append(str(obj))
        node.children.append("/EOC")
        return node

    def visit_callable(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        node.children.append(pickle.dumps(obj))
        node.children.append("/EOC")
        return node

    def visit_custom_obj(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if is_pickable(obj):
            reduced = obj.__reduce_ex__(4)
            if not isinstance(obj, pandas.core.indexes.range.RangeIndex):
                node.id_obj = id(obj)
                node.check_value_only = False

            if isinstance(reduced, str):
                node.children.append(reduced)
                return node

            for item in reduced[1:]:
                child = object_state.get_object_state(item, visited=visited, visitor=self, include_id=False)
                node.children.append(child)
            node.children.append("/EOC")
        return node

    def visit_other(self, obj, visited: dict, include_id: bool, hash_state: None) -> GraphNode:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        # node.children.append(str(obj))
        node.children.append(pickle.dumps(obj))
        node.children.append("/EOC")
        return node


def convert_idgraph_to_list(node: GraphNode, ret_list: List[Any], visited: set) -> None:
    # pre oder

    if not node.check_value_only:
        ret_list.append(node.id_obj)

    ret_list.append(node.obj_type)

    if id(node) in visited:
        ret_list.append("CYCLIC_REFERENCE")
        return

    visited.add(id(node))

    for child in node.children:
        if isinstance(child, GraphNode):
            convert_idgraph_to_list(child, ret_list, visited)
        else:
            ret_list.append(child)


def compare_idgraph(idGraph1: GraphNode, idGraph2: GraphNode) -> bool:
    ls1: list = []
    ls2: list = []

    convert_idgraph_to_list(idGraph1, ls1, set())
    convert_idgraph_to_list(idGraph2, ls2, set())

    if len(ls1) != len(ls2):
        # print("Diff lengths of idgraph")
        return False

    for i in range(len(ls1)):
        if pandas.isnull(ls1[i]):
            if pandas.isnull(ls2[i]):
                continue
            # print("Diff: ", ls1[i], ls2[i])
            return False
        if ls1[i] != ls2[i]:
            # print("Diff: ", ls1[i], ls2[i])
            return False

    return True
