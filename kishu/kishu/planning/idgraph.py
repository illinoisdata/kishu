from __future__ import annotations

import pandas
import pickle
import xxhash


class GraphNode:

    def __init__(self, obj_type=type(None), id_obj=0, check_value_only=False):
        self.id_obj = id_obj
        self.children = []
        self.check_value_only = check_value_only
        self.obj_type = obj_type

    def convert_to_list(self):
        ls = []
        GraphNode._convert_idgraph_to_list(self, ls, set())
        return ls

    def id_set(self):
        return set([i for i in self.convert_to_list() if isinstance(i, int)])

    def is_overlap(self, other: GraphNode) -> bool:
        if self.id_set().intersection(other.id_set()):
            return True
        return False

    def is_root_equals(self, other):
        """
            Compare only the root notes of 2 ID graphs.
        """
        if other is None:
            return False
        return self.id_obj == other.id_obj and self.obj_type == other.obj_type

    def __eq__(self, other):
        return GraphNode._compare_idgraph(self, other)

    @staticmethod
    def _convert_idgraph_to_list(node: GraphNode, ret_list, visited: set):
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
                GraphNode._convert_idgraph_to_list(child, ret_list, visited)
            else:
                ret_list.append(child)

    @staticmethod
    def _compare_idgraph(idGraph1: GraphNode, idGraph2: GraphNode) -> bool:
        ls1 = idGraph1.convert_to_list()
        ls2 = idGraph2.convert_to_list()

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


def is_pickable(obj):
    try:
        if callable(obj):
            return False

        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False


def get_object_state(obj, visited: dict, include_id=True) -> GraphNode:

    if id(obj) in visited.keys():
        return visited[id(obj)]

    if isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis))):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    elif isinstance(obj, tuple):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        for item in obj:
            child = get_object_state(item, visited, include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, list):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False

        for item in obj:
            child = get_object_state(item, visited, include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, set):
        node = GraphNode(obj_type=type(obj), id_obj=id(obj),
                         check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        for item in obj:
            child = get_object_state(item, visited, include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, dict):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False

        for key, value in obj.items():
            child = get_object_state(key, visited, include_id)
            node.children.append(child)
            child = get_object_state(value, visited, include_id)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, (bytes, bytearray)):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    elif isinstance(obj, type):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        node.children.append(str(obj))
        node.children.append("/EOC")
        return node

    elif callable(obj):
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        # This will break if obj is not pickleable. Commenting out for now.
        # node.children.append(pickle.dumps(obj))
        node.children.append("/EOC")
        return node

    elif hasattr(obj, '__reduce_ex__'):
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
                child = get_object_state(item, visited, False)
                node.children.append(child)
            node.children.append("/EOC")
        return node

    elif hasattr(obj, '__reduce__'):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if is_pickable(obj):
            reduced = obj.__reduce__()
            node.id_obj = id(obj)

            if isinstance(reduced, str):
                node.children.append(reduced)
                return node

            for item in reduced[1:]:
                child = get_object_state(item, visited, False)
                node.children.append(child)

            node.children.append("/EOC")
        return node

    elif hasattr(obj, '__getstate__'):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        node.id_obj = id(obj)

        for attr_name, attr_value in obj.__getstate__().items():
            node.children.append(attr_name)
            child = get_object_state(attr_value, visited, False)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif hasattr(obj, '__dict__'):
        # visited.add(id(obj))
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        node.id_obj = id(obj)

        for attr_name, attr_value in obj.__dict__.items():
            node.children.append(attr_name)
            child = get_object_state(attr_value, visited)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    else:
        node = GraphNode(obj_type=type(obj), check_value_only=True)
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        node.children.append(pickle.dumps(obj))
        node.children.append("/EOC")
        return node


def build_object_hash(obj, visited: set, include_id=True, hashed=xxhash.xxh32()):
    if id(obj) in visited:
        hashed.update(str(type(obj)))
        if include_id:
            hashed.update(str(id(obj)))

    elif isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis))):
        hashed.update(str(type(obj)))
        hashed.update(str(obj))
        hashed.update("/EOC")

    elif isinstance(obj, tuple):
        hashed.update(str(type(obj)))
        for item in obj:
            build_object_hash(item, visited, include_id, hashed)

        hashed.update("/EOC")

    elif isinstance(obj, list):
        hashed.update(str(type(obj)))
        visited.add(id(obj))
        if include_id:
            hashed.update(str(id(obj)))

        for item in obj:
            build_object_hash(item, visited, include_id, hashed)

        hashed.update("/EOC")

    elif isinstance(obj, set):
        hashed.update(str(type(obj)))
        visited.add(id(obj))
        if include_id:
            hashed.update(str(id(obj)))

        for item in obj:
            build_object_hash(item, visited, include_id, hashed)

        hashed.update("/EOC")

    elif isinstance(obj, dict):
        hashed.update(str(type(obj)))
        visited.add(id(obj))
        if include_id:
            hashed.update(str(id(obj)))

        for key, value in obj.items():
            build_object_hash(key, visited, include_id, hashed)
            build_object_hash(value, visited, include_id, hashed)

        hashed.update("/EOC")

    elif isinstance(obj, (bytes, bytearray)):
        hashed.update(str(type(obj)))
        hashed.update(obj)
        hashed.update("/EOC")

    elif isinstance(obj, type):
        hashed.update(str(type(obj)))
        hashed.update(str(obj))

    elif callable(obj):
        hashed.update(str(type(obj)))
        if include_id:
            visited.add(id(obj))
            hashed.update(str(id(obj)))

        hashed.update("/EOC")

    elif hasattr(obj, '__reduce_ex__'):
        visited.add(id(obj))
        hashed.update(str(type(obj)))

        if is_pickable(obj):
            reduced = obj.__reduce_ex__(4)
            if not isinstance(obj, pandas.core.indexes.range.RangeIndex):
                hashed.update(str(id(obj)))

            if isinstance(reduced, str):
                hashed.update(reduced)
                return

            for item in reduced[1:]:
                build_object_hash(item, visited, False, hashed)

            hashed.update("/EOC")

    elif hasattr(obj, '__reduce__'):
        visited.add(id(obj))
        hashed.update(str(type(obj)))
        if is_pickable(obj):
            reduced = obj.__reduce__()
            hashed.update(str(id(obj)))

            if isinstance(reduced, str):
                hashed.udpate(reduced)
                return

            for item in reduced[1:]:
                build_object_hash(item, visited, False, hashed)

            hashed.update("/EOC")

    else:
        print("Comes here")
        visited.add(id(obj))
        hashed.update(str(type(obj)))
        if include_id:
            hashed.update(str(id(obj)))
        hashed.update(pickle.dumps(obj))
        hashed.update("/EOC")


def get_object_hash(obj):
    x = xxhash.xxh32()
    build_object_hash(obj, set(), True, x)
    return x
