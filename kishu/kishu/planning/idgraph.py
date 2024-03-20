from __future__ import annotations

from typing import Any, List, Optional
from types import GeneratorType

import numpy
import scipy
import torch
import pandas
import pickle
import uuid
import xxhash


PRIMITIVES = (type(None), int, float, bool, str, bytes)


class GraphNode:

    def __init__(self, obj_type=type(None), id_obj: Optional[int] = None):
        self.id_obj = id_obj
        self.children: List[Any] = []
        self.obj_type = obj_type
        self.cached_id_set: Optional[Set[Any]] = None

        self.cached_list_check_id_obj: Optional[List[Any]] = None
        self.cached_list_not_check_id_obj: Optional[List[Any]] = None

    def convert_to_list(self, check_id_obj=True, check_value=True):
        if check_value:
            ls = []
            GraphNode._convert_idgraph_to_list(self, ls, set(), check_id_obj, check_value)
            return ls

        if check_id_obj:
            if not self.cached_list_check_id_obj:
                ls = []
                GraphNode._convert_idgraph_to_list(self, ls, set(), check_id_obj, check_value)
                self.cached_list_check_id_obj = ls
            return self.cached_list_check_id_obj

        if not self.cached_list_not_check_id_obj:
            ls = []
            GraphNode._convert_idgraph_to_list(self, ls, set(), check_id_obj, check_value)
            self.cached_list_not_check_id_obj = ls
        return self.cached_list_not_check_id_obj

    def id_set(self) -> Set[Any]:
        if not self.cached_id_set:
            self.cached_id_set = set([i for i in self.convert_to_list(check_value=False) if isinstance(i, int)])
        return self.cached_id_set

    def is_overlap(self, other: GraphNode) -> bool:
        if self.id_set().intersection(other.id_set()):
            return True
        return False

    def is_root_id_and_type_equals(self, other):
        """
            Compare only the ID and type fields of root nodes of 2 ID graphs.
            Used for detecting non-overwrite modifications.
        """
        if other is None:
            return False
        return self.id_obj == other.id_obj and self.obj_type == other.obj_type

    def __eq__(self, other):
        return GraphNode._compare_idgraph(self, other, check_id_obj=True)

    @staticmethod
    def _convert_idgraph_to_list(node: GraphNode, ret_list, visited: set, check_id_obj=True, check_value=True):
        # pre oder

        if node.id_obj and check_id_obj:
            ret_list.append(node.id_obj)

        ret_list.append(node.obj_type)

        if id(node) in visited:
            ret_list.append("CYCLIC_REFERENCE")
            return

        visited.add(id(node))

        for child in node.children:
            if isinstance(child, GraphNode):
                GraphNode._convert_idgraph_to_list(child, ret_list, visited, check_id_obj, check_value)
            else:
                if check_value or node.obj_type not in PRIMITIVES: 
                    ret_list.append(child)

    @staticmethod
    def _compare_idgraph(idGraph1: GraphNode, idGraph2: GraphNode, check_id_obj=True) -> bool:
        ls1 = idGraph1.convert_to_list(check_id_obj)
        ls2 = idGraph2.convert_to_list(check_id_obj)

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


def value_equals(idGraph1: GraphNode, idGraph2: GraphNode):
    """
        Compare only the object values (not memory addresses) of 2 ID graphs.
        Notably, this identifies two value-wise equal object stored in different memory locations
        as equal.
        Used by frontend to display variable diffs.
    """
    return GraphNode._compare_idgraph(idGraph1, idGraph2, check_id_obj=False)


def get_object_state(obj, visited: dict, include_id=True, first_creation=False) -> GraphNode:

    if id(obj) in visited.keys():
        return visited[id(obj)]

    if isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis))):
        node = GraphNode(obj_type=type(obj))
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    elif isinstance(obj, tuple):
        node = GraphNode(obj_type=type(obj))
        for item in obj:
            child = get_object_state(item, visited, include_id, first_creation)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, list):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)

        for item in obj:
            child = get_object_state(item, visited, include_id, first_creation)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, set):
        node = GraphNode(obj_type=type(obj), id_obj=id(obj))
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
        for item in obj:
            child = get_object_state(item, visited, include_id, first_creation)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, dict):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)

        for key, value in obj.items():
            child = get_object_state(key, visited, include_id, first_creation)
            node.children.append(child)
            child = get_object_state(value, visited, include_id, first_creation)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    elif isinstance(obj, (bytes, bytearray)):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        node.children.append(obj)
        node.children.append("/EOC")
        return node

    elif isinstance(obj, type):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        node.children.append(str(obj))
        node.children.append("/EOC")
        return node

    elif issubclass(type(obj), numpy.dtype):
        # Numpy dtypes are dynamically generated. Don't store their memory addresses.
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        node.children.append(str(obj))
        node.children.append("/EOC")
        return node

    if isinstance(obj, pandas.DataFrame):
        if first_creation:
            for (_, col) in obj.items():
                col.__array__().flags.writeable = False

        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node
        for (_, col) in obj.items():
            node.children.append(str(col.__array__().flags.writeable))
            col.__array__().flags.writeable = False
        node.children.append("/EOC")
        return node

    if isinstance(obj, pandas.Series):
        if first_creation:
            obj.__array__().flags.writeable = False

        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node
        node.children.append(str(obj.__array__().flags.writeable))
        obj.__array__().flags.writeable = False
        node.children.append("/EOC")
        return node

    if isinstance(obj, numpy.ndarray):
        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node

        # create hash
        h = xxhash.xxh3_128()
        h.update(numpy.ascontiguousarray(obj.data))
        node.children.append(h.intdigest())
        node.children.append("/EOC")
        return node

    if isinstance(obj, scipy.sparse.csr_matrix):
        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node

        # create hash
        h = xxhash.xxh3_128()
        h.update(numpy.ascontiguousarray(obj.data))
        node.children.append(h.intdigest())
        node.children.append("/EOC")
        return node

    if isinstance(obj, torch.Tensor):
        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node

        # create hash
        h = xxhash.xxh3_128()
        h.update(numpy.ascontiguousarray(obj.data))
        node.children.append(h.intdigest())
        node.children.append("/EOC")
        return node

    # elif isinstance(obj, GeneratorType):
    #     # Hack for the generator class to make it identify as always modified.
    #     node = GraphNode(obj_type=type(obj), id_obj = uuid.uuid4().hex)
    #     visited[id(obj)] = node
    #     node.children.append(str(obj))
    #     node.children.append("/EOC")
    #     return node

    elif callable(obj):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
        # This will break if obj is not pickleable. Commenting out for now.
        # node.children.append(pickle.dumps(obj))
        node.children.append("/EOC")
        return node

    elif hasattr(obj, '__reduce_ex__'):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if is_pickable(obj):
            reduced = obj.__reduce_ex__(4)
            if not isinstance(obj, pandas.core.indexes.range.RangeIndex):
                node.id_obj = id(obj)

            if isinstance(reduced, str):
                node.children.append(reduced)
                return node

            for item in reduced[1:]:
                child = get_object_state(item, visited, include_id=False, first_creation=first_creation)
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
                child = get_object_state(item, visited, include_id=False, first_creation=first_creation)
                node.children.append(child)

            node.children.append("/EOC")
        return node

    elif hasattr(obj, '__getstate__'):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        node.id_obj = id(obj)

        for attr_name, attr_value in obj.__getstate__().items():
            node.children.append(attr_name)
            child = get_object_state(attr_value, visited, include_id=False, first_creation=first_creation)
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
            child = get_object_state(attr_value, visited, first_creation=first_creation)
            node.children.append(child)

        node.children.append("/EOC")
        return node

    else:
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
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
