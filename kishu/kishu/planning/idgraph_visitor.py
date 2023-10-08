import hashlib
import pandas
import pickle
import xxhash
from kishu.planning.visitor import Visitor
import kishu.planning.object_state as object_state

# called idgraph_visitor.py


def is_pickable(obj):
    try:
        if callable(obj):
            return False

        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False


class GraphNode:

    def __init__(self, obj_type=type(None), id_obj=0, check_value_only=False):
        self.id_obj = id_obj
        self.children = []
        self.check_value_only = check_value_only
        self.obj_type = obj_type

    def __eq__(self, other):
        return compare_idgraph(self, other)


class idgraph(Visitor):
    def check_visited(self, visited: dict, obj_id, include_id):
        if obj_id in visited.keys():
            return True, visited[obj_id]
        else:
            return False, 0

    def visit_primitive(self, obj):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    def visit_tuple(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        for item in obj:
            child = object_state.get_object_state(
                item, visited, visitor=self, include_id=include_id)

            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_list(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False

        for item in obj:
            child = object_state.get_object_state(
                item, visited, visitor=self, include_id=include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_set(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), id_obj=id(obj),
                         check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        for item in sorted(obj):
            child = object_state.get_object_state(
                item, visited, visitor=self, include_id=include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_dict(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False

        for key, value in sorted(obj.items()):
            node.children.append(key)
            child = object_state.get_object_state(
                value, visited, visitor=self, include_id=include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    def visit_byte(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    def visit_type(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        node.children.append(str(obj))
        node.children.append("/EOC")
        return node

    def visit_callable(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        node.children.append(pickle.dumps(obj))
        node.children.append("/EOC")
        return node

    def visit_custom_obj(self, obj, visited, include_id, update_state):
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
                child = object_state.get_object_state(
                    item, visited=visited, visitor=self, include_id=False)
                node.children.append(child)
            node.children.append("/EOC")
        return node

    def visit_other(self, obj, visited, include_id, update_state):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        # node.children.append(str(obj))
        node.children.append(pickle.dumps(obj))
        node.children.append("/EOC")
        return node


def convert_idgraph_to_list(node: GraphNode, ret_list, visited: set):
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
