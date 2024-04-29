from __future__ import annotations

import cloudpickle
import matplotlib.pyplot as plt
import numpy
import pandas
import pickle
import re
import scipy
import sklearn.tree
import sklearn.feature_extraction
import sklearn.ensemble
import torch
import uuid
import xxhash

from matplotlib.contour import QuadContourSet
from typing import Any, List, Optional, Set
from types import GeneratorType, FunctionType


PRIMITIVES = (type(None), int, float, bool, str, bytes)


class GraphNode:

    def __init__(self, obj_type=type(None), id_obj: Optional[int] = None):
        self.id_obj = id_obj
        self.children: List[Any] = []
        self.obj_type = obj_type

        self.cached_id_set: Optional[Set[Any]] = None
        self.cached_list: Optional[List[Any]] = None
        self.cached_list_not_check_value: Optional[List[Any]] = None
        self.cached_list_not_check_id_obj: Optional[List[Any]] = None

    def convert_to_list(self, check_id_obj=True, check_value=True):
        # initialize
        if not self.cached_list:
            ls = []
            ls_no_check_value = []
            ls_no_check_id_obj = []
            GraphNode._convert_idgraph_to_list(self, ls, ls_no_check_value, ls_no_check_id_obj, set())
            self.cached_list = ls
            self.cached_list_not_check_value = ls_no_check_value
            self.cached_list_not_check_id_obj = ls_no_check_id_obj

        if check_value and check_id_obj:
            return self.cached_list

        if check_id_obj:
            return self.cached_list_not_check_value

        if check_value:
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
    def _convert_idgraph_to_list(
        node: GraphNode,
        ret_list,
        no_check_value_ret_list,
        no_check_id_obj_ret_list,
        visited: set,
    ):
        # pre order
        if node.id_obj:
            ret_list.append(node.id_obj)
            no_check_value_ret_list.append(node.id_obj)

        ret_list.append(node.obj_type)
        no_check_value_ret_list.append(node.obj_type)
        no_check_id_obj_ret_list.append(node.obj_type)

        if id(node) in visited:
            ret_list.append("CYCLIC_REFERENCE")
            no_check_value_ret_list.append("CYCLIC_REFERENCE")
            no_check_id_obj_ret_list.append("CYCLIC_REFERENCE")
            return

        visited.add(id(node))

        for child in node.children:
            if isinstance(child, GraphNode):
                GraphNode._convert_idgraph_to_list(child, ret_list, no_check_value_ret_list, no_check_id_obj_ret_list, visited)
            else:
                ret_list.append(child)
                no_check_id_obj_ret_list.append(child)

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
    except:
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

    if isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis), FunctionType)):
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
        # dtypes are dynamically generated. Don't store their memory addresses.
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
        """
            Pandas dataframe dirty bit hack. We can use the writeable flag as a dirty bit to check for updates
            (as any Pandas operation will flip the bit back to True).
            notably, this may prevent the usage of certain slicing operations; however, they are rare compared
            to boolean indexing, hence this tradeoff is acceptable.
        """
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

    if isinstance(obj, sklearn.tree._classes.DecisionTreeRegressor):
        """
            Hack for the sklearn decision tree. It contains only a list of tree splitting boundaries which are unaccesible
            through member functions, so we early stop and pickle the list instead (as it is very unlikely to be shared via
            reference with other variables); otherwise ID graph construction may be very slow.
        """
        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node

        node.children.append(cloudpickle.dumps(obj))
        if hasattr(obj, 'tree_'):
            child = get_object_state(obj.tree_, visited, include_id, first_creation)
            node.children.append(child)
        node.children.append("/EOC")
        return node

    if isinstance(obj, plt.Figure):
        """
            Same hack as sklearn decision tree.
        """
        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node

        node.children.append(cloudpickle.dumps(obj))
        for item in obj.axes:
            child = get_object_state(item, visited, include_id=False, first_creation=first_creation)
            node.children.append(child)
        node.children.append("/EOC")
        return node

    if isinstance(obj, (
        sklearn.ensemble.RandomForestRegressor,
        sklearn.feature_extraction.text.CountVectorizer,
        plt.Axes,
        QuadContourSet
    )):
        """
            Same hack as sklearn decision tree.
        """
        node = GraphNode(obj_type=type(obj))
        node.id_obj = id(obj)
        visited[id(obj)] = node

        node.children.append(cloudpickle.dumps(obj))
        node.children.append("/EOC")
        return node

    if isinstance(obj, numpy.ndarray):
        try:
            node = GraphNode(obj_type=type(obj))
            node.id_obj = id(obj)
            visited[id(obj)] = node

            h = xxhash.xxh3_128()
            h.update(numpy.ascontiguousarray(obj.data))
            node.children.append(h.intdigest())
            node.children.append("/EOC")
            return node
        except:
            # If hashing fails, continue recursing into children.
            pass

    if isinstance(obj, scipy.sparse.csr_matrix):
        try:
            node = GraphNode(obj_type=type(obj))
            node.id_obj = id(obj)
            visited[id(obj)] = node
    
            # create hash
            h = xxhash.xxh3_128()
            h.update(numpy.ascontiguousarray(obj.data))
            node.children.append(h.intdigest())
            node.children.append("/EOC")
            return node
        except:
            # If hashing fails, continue recursing into children.
            pass

    if isinstance(obj, torch.Tensor):
        try:
            node = GraphNode(obj_type=type(obj))
            node.id_obj = id(obj)
            visited[id(obj)] = node
    
            # create hash
            h = xxhash.xxh3_128()
            h.update(numpy.ascontiguousarray(obj.cpu().data))
            node.children.append(h.intdigest())
            node.children.append("/EOC")
            return node
        except:
            # If hashing fails, continue recursing into children.
            pass


    elif isinstance(obj, (GeneratorType, re.Pattern)):
        # Hack for unobservable unserializable objects to make them identify as always modified on access.
        node = GraphNode(obj_type=type(obj), id_obj = uuid.uuid4().hex)
        visited[id(obj)] = node
        node.children.append("/EOC")
        return node

    elif callable(obj):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if include_id:
            node.id_obj = id(obj)
        try:
            node.children.append(pickle.dumps(obj))
        except:
            node.children.append(uuid.uuid4().hex)
        node.children.append("/EOC")
        return node

    elif hasattr(obj, '__reduce_ex__'):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if is_pickable(obj):
            try:
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
            except:
                node.children.append(uuid.uuid4().hex)
                node.children.append("/EOC")
        else:
            node.children.append(uuid.uuid4().hex)
            node.children.append("/EOC")
        return node

    elif hasattr(obj, '__reduce__'):
        node = GraphNode(obj_type=type(obj))
        visited[id(obj)] = node
        if is_pickable(obj):
            try:
                reduced = obj.__reduce__()
                node.id_obj = id(obj)
    
                if isinstance(reduced, str):
                    node.children.append(reduced)
                    return node
    
                for item in reduced[1:]:
                    child = get_object_state(item, visited, include_id=False, first_creation=first_creation)
                    node.children.append(child)
    
                node.children.append("/EOC")
            except:
                node.children.append(uuid.uuid4().hex)
                node.children.append("/EOC")
        else:
            node.children.append(uuid.uuid4().hex)
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
        try:
            node.children.append(cloudpickle.dumps(obj))
        except:
            node.children.append(uuid.uuid4().hex)
        node.children.append("/EOC")
        return node

    node = GraphNode(obj_type=type(obj))
    visited[id(obj)] = node
    if include_id:
        node.id_obj = id(obj)
    try:
        node.children.append(cloudpickle.dumps(obj))
    except:
        node.children.append(uuid.uuid4().hex)
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
