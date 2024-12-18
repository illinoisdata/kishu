import pickle
from typing import Optional

import pandas
import xxhash

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


class hash_vis(Visitor):
    def check_visited(
        self, visited: set, obj_id: int, obj_type: type, include_id: bool, hash_state: xxhash.xxh32
    ) -> Optional[xxhash.xxh32]:
        if obj_id in visited:
            hash_state.update(str(obj_type))
            if include_id:
                hash_state.update(str(obj_id))
            return hash_state
        else:
            return None

    def visit_primitive(self, obj, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        hash_state.update(str(obj))
        hash_state.update("/EOC")
        return hash_state

    def visit_tuple(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        for item in obj:
            object_state.get_object_state(item, visited, visitor=self, include_id=include_id, hash_state=hash_state)

        hash_state.update("/EOC")
        return hash_state

    def visit_list(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        visited.add(id(obj))
        if include_id:
            hash_state.update(str(id(obj)))

        for item in obj:
            object_state.get_object_state(item, visited, visitor=self, include_id=include_id, hash_state=hash_state)

        hash_state.update("/EOC")
        return hash_state

    def visit_set(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        visited.add(id(obj))
        if include_id:
            hash_state.update(str(id(obj)))

        for item in sorted(obj):
            object_state.get_object_state(item, visited, visitor=self, include_id=include_id, hash_state=hash_state)

        hash_state.update("/EOC")
        return hash_state

    def visit_dict(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        visited.add(id(obj))
        if include_id:
            hash_state.update(str(id(obj)))

        for key, value in sorted(obj.items()):
            object_state.get_object_state(key, visited, visitor=self, include_id=include_id, hash_state=hash_state)
            object_state.get_object_state(value, visited, visitor=self, include_id=include_id, hash_state=hash_state)

        hash_state.update("/EOC")
        return hash_state

    def visit_byte(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        hash_state.update(obj)
        hash_state.update("/EOC")
        return hash_state

    def visit_type(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        hash_state.update(str(obj))
        return hash_state

    def visit_callable(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        hash_state.update(str(type(obj)))
        if include_id:
            visited.add(id(obj))
            hash_state.update(str(id(obj)))

        hash_state.update("/EOC")
        return hash_state

    def visit_custom_obj(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        visited.add(id(obj))
        hash_state.update(str(type(obj)))

        if is_pickable(obj):
            reduced = obj.__reduce_ex__(4)
            if not isinstance(obj, pandas.core.indexes.range.RangeIndex):
                hash_state.update(str(id(obj)))

            if isinstance(reduced, str):
                hash_state.update(reduced)
                return hash_state

            for item in reduced[1:]:
                object_state.get_object_state(item, visited, visitor=self, include_id=False, hash_state=hash_state)

            hash_state.update("/EOC")
        return hash_state

    def visit_other(self, obj, visited: set, include_id: bool, hash_state: xxhash.xxh32) -> xxhash.xxh32:
        visited.add(id(obj))
        hash_state.update(str(type(obj)))
        if include_id:
            hash_state.update(str(id(obj)))
        hash_state.update(pickle.dumps(obj))
        hash_state.update("/EOC")
        return hash_state
