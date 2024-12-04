from __future__ import annotations

import pickle
import re
from dataclasses import dataclass, field
from functools import cached_property
from types import FunctionType, GeneratorType
from typing import Any, List, Optional

import numpy
import pandas
import xxhash

from kishu.storage.config import Config


@dataclass(frozen=True)
class ClassInstance:
    name: str
    module: str

    @staticmethod
    def from_object(obj: Any) -> ClassInstance:
        return ClassInstance(type(obj).__name__, type(obj).__module__)


KISHU_DEFAULT_PICKLES = {
    ClassInstance("sklearn.tree._classes", "DecisionTreeRegressor"),
    ClassInstance("sklearn.ensemble", "RandomForestRegressor"),
    ClassInstance("sklearn.feature_extraction.text", "CountVectorizer"),
    ClassInstance("matplotlib.pyplot", "Axes"),
    ClassInstance("matplotlib.contour", "QuadContourSet"),
}


KISHU_DEFAULT_ARRAYTYPES = {
    ClassInstance("numpy", "ndarray"),
    ClassInstance("torch", "Tensor"),
    ClassInstance("scipy.sparse", "csr_matrix"),
    ClassInstance("scipy.sparse", "csc_matrix"),
    ClassInstance("scipy.sparse", "lil_matrix"),
}


@dataclass
class CyclicReference:
    def __eq__(self, other):
        return isinstance(other, CyclicReference)


@dataclass
class EndOfChildren:
    def __eq__(self, other):
        return isinstance(other, EndOfChildren)


@dataclass
class UncomparableObj:
    def __eq__(self, other):
        return False


@dataclass
class DirtyColumn:
    is_dirty: bool

    def __eq__(self, other):
        # If the new dataframe (i.e., other) has the dirty bit unset, the two dataframes
        # are assumed unequal (regardless of the value of the dirty bit of the old
        # dataframe).
        return not other.is_dirty


@dataclass(frozen=True)
class ObjectId:
    obj_id: int

    def __eq__(self, other):
        if not isinstance(other, ObjectId):
            return False
        return self.obj_id == other.obj_id


@dataclass
class GraphNode:
    obj_id: Optional[ObjectId]
    obj_type: Any
    children: List[Any] = field(default_factory=lambda: [])

    def convert_to_list(self):
        ls = []
        GraphNode._convert_idgraph_to_list(self, ls, set())  # In-place populated list  # visited
        return ls

    @staticmethod
    def _convert_idgraph_to_list(node: GraphNode, ret_list, visited: set):
        # pre oder
        ret_list.append(node.obj_id)
        ret_list.append(node.obj_type)

        if id(node) in visited:
            ret_list.append(CyclicReference())
            return

        visited.add(id(node))

        for child in node.children:
            if isinstance(child, GraphNode):
                GraphNode._convert_idgraph_to_list(child, ret_list, visited)
            else:
                ret_list.append(child)

    @staticmethod
    def get_object_state(obj, visited: dict) -> GraphNode:

        if id(obj) in visited.keys():
            return visited[id(obj)]

        if isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis), bytes, bytearray, type)):
            node = GraphNode(None, type(obj), [obj, EndOfChildren()])
            visited[id(obj)] = node
            return node

        if isinstance(obj, FunctionType):
            node = GraphNode(ObjectId(id(obj)), type(obj), [obj, EndOfChildren()])
            visited[id(obj)] = node
            return node

        if issubclass(type(obj), numpy.dtype):
            # Numpy dtypes are dynamically generated. Don't store their memory addresses.
            node = GraphNode(None, type(obj), [str(obj), EndOfChildren()])
            visited[id(obj)] = node
            return node

        if isinstance(obj, tuple):
            node = GraphNode(None, type(obj))
            visited[id(obj)] = node
            node.children = [GraphNode.get_object_state(item, visited) for item in obj] + [EndOfChildren()]
            return node

        if isinstance(obj, (list, set)):
            node = GraphNode(ObjectId(id(obj)), type(obj))
            visited[id(obj)] = node
            node.children = [GraphNode.get_object_state(item, visited) for item in obj] + [EndOfChildren()]
            return node

        if isinstance(obj, dict):
            node = GraphNode(ObjectId(id(obj)), type(obj))
            visited[id(obj)] = node
            node.children = [GraphNode.get_object_state(item, visited) for pair in obj.items() for item in pair] + [
                EndOfChildren()
            ]
            return node

        if isinstance(obj, (GeneratorType, re.Pattern)):
            # Unobservable unserializable objects are always identified as modified on access by appending a random hash as
            # child.
            node = GraphNode(ObjectId(id(obj)), type(obj), [UncomparableObj(), EndOfChildren()])
            visited[id(obj)] = node
            return node

        if isinstance(obj, pandas.DataFrame) and Config.get("IDGRAPH", "pandas_df_hack", True):
            # Pandas dataframe dirty bit hack. We can use the writeable flag as a dirty bit to check for updates
            # (as any Pandas operation will flip the bit back to True).
            # Notably, this may prevent the usage of certain slicing operations; however, they are rare compared
            # to boolean indexing, hence this tradeoff is acceptable.
            node = GraphNode(
                ObjectId(id(obj)),
                type(obj),
                [DirtyColumn(col.__array__().flags.writeable) for (_, col) in obj.items()] + [EndOfChildren()],
            )
            visited[id(obj)] = node
            for _, col in obj.items():
                col.__array__().flags.writeable = False
            return node

        if ClassInstance.from_object(obj) in Config.get("IDGRAPH", "arraytype_hack", KISHU_DEFAULT_ARRAYTYPES):
            # Hash hack for arraytypes. They are hashed instead of recursing into the array themselves.
            # Like the pandas dataframe hack, this may incur correctness loss if a field inside the array is assigned
            # to another variable (and causing an overlap); however, this is rare in notebooks and the speedup this brings
            # is significant.
            node = GraphNode(ObjectId(id(obj)), type(obj))
            visited[id(obj)] = node
            h = xxhash.xxh3_128()

            # xxhash's update works with arbitrary arrays, even object arrays
            h.update(numpy.ascontiguousarray(obj.data))  # type: ignore

            node.children.append(h.intdigest())
            node.children.append(EndOfChildren())
            return node

        if ClassInstance.from_object(obj) in Config.get("IDGRAPH", "pickle_hack", KISHU_DEFAULT_PICKLES):
            # Hack for a (configurable list of) objects which typically contain many deeply nested fields (e.g., lists) which
            # are inaccessible through member functions, so we early stop and pickle it instead (as it is very unlikely to be
            # shared via reference with other variables); otherwise ID graph construction may be very slow.
            # Note that this potentially incurs correctness losses.
            node = GraphNode(ObjectId(id(obj)), type(obj), [GraphNode.pickle_object(obj), EndOfChildren()])
            visited[id(obj)] = node
            return node

        if callable(obj):
            node = GraphNode(ObjectId(id(obj)), type(obj), [GraphNode.pickle_object(obj), EndOfChildren()])
            visited[id(obj)] = node
            return node

        if hasattr(obj, "__reduce_ex__"):
            node = GraphNode(ObjectId(id(obj)), obj_type=type(obj))
            visited[id(obj)] = node
            if GraphNode.is_pickable(obj):
                reduced = obj.__reduce_ex__(4)

                if isinstance(reduced, str):
                    node.children.append(reduced)
                    return node

                for item in reduced[1:]:
                    child = GraphNode.get_object_state(item, visited)
                    node.children.append(child)
                node.children.append(EndOfChildren())
            return node

        if hasattr(obj, "__reduce__"):
            node = GraphNode(ObjectId(id(obj)), obj_type=type(obj))
            visited[id(obj)] = node
            if GraphNode.is_pickable(obj):
                reduced = obj.__reduce__()

                if isinstance(reduced, str):
                    node.children.append(reduced)
                    return node

                for item in reduced[1:]:
                    child = GraphNode.get_object_state(item, visited)
                    node.children.append(child)

                node.children.append(EndOfChildren())
            return node

        if hasattr(obj, "__getstate__"):
            node = GraphNode(ObjectId(id(obj)), type(obj))
            visited[id(obj)] = node

            for attr_name, attr_value in obj.__getstate__().items():
                node.children.append(attr_name)
                child = GraphNode.get_object_state(attr_value, visited)
                node.children.append(child)

            node.children.append(EndOfChildren())
            return node

        if hasattr(obj, "__dict__"):
            node = GraphNode(ObjectId(id(obj)), type(obj))
            visited[id(obj)] = node

            for attr_name, attr_value in obj.__dict__.items():
                node.children.append(attr_name)
                child = GraphNode.get_object_state(attr_value, visited)
                node.children.append(child)

            node.children.append(EndOfChildren())
            return node

        else:
            # Fallback node generation method.
            node = GraphNode(ObjectId(id(obj)), type(obj), [GraphNode.pickle_object(obj), EndOfChildren()])
            visited[id(obj)] = node
            return node

    @staticmethod
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
                GraphNode.build_object_hash(item, visited, include_id, hashed)

            hashed.update("/EOC")

        elif isinstance(obj, list):
            hashed.update(str(type(obj)))
            visited.add(id(obj))
            if include_id:
                hashed.update(str(id(obj)))

            for item in obj:
                GraphNode.build_object_hash(item, visited, include_id, hashed)

            hashed.update("/EOC")

        elif isinstance(obj, set):
            hashed.update(str(type(obj)))
            visited.add(id(obj))
            if include_id:
                hashed.update(str(id(obj)))

            for item in obj:
                GraphNode.build_object_hash(item, visited, include_id, hashed)

            hashed.update("/EOC")

        elif isinstance(obj, dict):
            hashed.update(str(type(obj)))
            visited.add(id(obj))
            if include_id:
                hashed.update(str(id(obj)))

            for key, value in obj.items():
                GraphNode.build_object_hash(key, visited, include_id, hashed)
                GraphNode.build_object_hash(value, visited, include_id, hashed)

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

        elif hasattr(obj, "__reduce_ex__"):
            visited.add(id(obj))
            hashed.update(str(type(obj)))

            if GraphNode.is_pickable(obj):
                reduced = obj.__reduce_ex__(4)
                if not isinstance(obj, pandas.core.indexes.range.RangeIndex):
                    hashed.update(str(id(obj)))

                if isinstance(reduced, str):
                    hashed.update(reduced)
                    return

                for item in reduced[1:]:
                    GraphNode.build_object_hash(item, visited, False, hashed)

                hashed.update("/EOC")

        elif hasattr(obj, "__reduce__"):
            visited.add(id(obj))
            hashed.update(str(type(obj)))
            if GraphNode.is_pickable(obj):
                reduced = obj.__reduce__()
                hashed.update(str(id(obj)))

                if isinstance(reduced, str):
                    hashed.udpate(reduced)
                    return

                for item in reduced[1:]:
                    GraphNode.build_object_hash(item, visited, False, hashed)

                hashed.update("/EOC")

        else:
            print("Comes here")
            visited.add(id(obj))
            hashed.update(str(type(obj)))
            if include_id:
                hashed.update(str(id(obj)))
            hashed.update(pickle.dumps(obj))
            hashed.update("/EOC")

    @staticmethod
    def is_pickable(obj):
        try:
            pickle.dumps(obj)
            return True
        except (pickle.PicklingError, AttributeError, TypeError):
            return False

    @staticmethod
    def pickle_object(obj):
        try:
            return pickle.dumps(obj)
        except (pickle.PicklingError, AttributeError, TypeError):
            return UncomparableObj()

    @staticmethod
    def get_object_hash(obj):
        x = xxhash.xxh32()
        GraphNode.build_object_hash(obj, set(), True, x)
        return x


@dataclass
class IdGraph:
    root: GraphNode

    @staticmethod
    def from_object(obj: Any) -> IdGraph:
        return IdGraph(GraphNode.get_object_state(obj, {}))

    @cached_property
    def _id_list(self):
        return self.root.convert_to_list()

    @cached_property
    def _value_equals_list(self):
        return [i for i in self._id_list if not isinstance(i, ObjectId)]

    @cached_property
    def _id_set(self):
        return set([i for i in self._id_list if isinstance(i, ObjectId)])

    def is_overlap(self, other: IdGraph) -> bool:
        return bool(self._id_set.intersection(other._id_set))

    def is_root_id_and_type_equals(self, other: IdGraph):
        """
        Compare only the ID and type fields of root nodes of 2 ID graphs.
        Used for detecting non-overwrite modifications.
        """
        return self.root.obj_id == other.root.obj_id and self.root.obj_type == other.root.obj_type

    def __eq__(self, other: Any):
        if not isinstance(other, IdGraph):
            return NotImplemented
        return self._id_list == other._id_list

    def value_equals(self, other: IdGraph):
        """
        Compare only the object values (not memory addresses) of 2 ID graphs.
        Notably, this identifies two value-wise equal object stored in different memory locations
        as equal.
        Used by frontend to display variable diffs.
        """
        return self._value_equals_list == other._value_equals_list
