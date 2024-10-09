import inspect
import pickle
import sys
import types
from typing import Any, Optional

import dill

from kishu.storage.config import Config


def _get_object_class(obj: Any) -> Optional[str]:
    obj_class = getattr(obj, "__class__", None)
    return str(obj_class) if obj_class else None


def _add_to_unserializable_list(obj: Any) -> None:
    if _get_object_class(obj):
        unserializable_class_list = Config.get("PROFILER", "excluded_classes", [])
        unserializable_class_list.append(_get_object_class(obj))
        Config.set("PROFILER", "excluded_classes", unserializable_class_list)


def _is_picklable(obj: Any) -> bool:
    """
    Checks whether an object is pickleable.
    """
    if _in_exclude_list(obj):
        return False
    if inspect.ismodule(obj):
        return True
    try:
        # This function can crash.
        is_picklable = dill.pickles(obj)

        # Add the unpicklable object to the config file.
        if not is_picklable and Config.get("PROFILER", "auto_add_unpicklable_object", True):
            _add_to_unserializable_list(obj)
        return is_picklable
    except Exception:
        pass

    # Double check with pickle library, which is slower but more robust.
    # TODO: remove this in the future, returning false when Dill fails.
    try:
        pickle.dumps(obj)
    except Exception:
        # Add the unpicklable object to the config file.
        if Config.get("PROFILER", "auto_add_unpicklable_object", True):
            _add_to_unserializable_list(obj)
        return False
    return True


def _in_exclude_list(obj: Any) -> bool:
    """
    Checks whether object is from a class which Dill reports is pickleable but is actually not.
    """
    return _get_object_class(obj) in Config.get("PROFILER", "excluded_classes", [])


def _get_memory_size(obj: Any, is_initialize: bool, visited: set) -> int:
    # same memory space should be calculated only once
    obj_id = id(obj)
    if obj_id in visited:
        return 0
    visited.add(obj_id)
    total_size = sys.getsizeof(obj)
    obj_type = type(obj)
    if obj_type in [int, float, str, bool, type(None)]:
        # if the original obj is not primitive, then the size is already included
        if not is_initialize:
            return 0
    else:
        if obj_type in [list, tuple, set]:
            for e in obj:
                total_size = total_size + _get_memory_size(e, False, visited)
        elif obj_type is dict:
            for k, v in obj.items():
                total_size = total_size + _get_memory_size(k, False, visited)
                total_size = total_size + _get_memory_size(v, False, visited)
        # function, method, class
        elif obj_type in [types.FunctionType, types.MethodType, types.BuiltinFunctionType, types.ModuleType] or isinstance(
            obj, type
        ):  # True if obj is a class
            pass
        # custom class instance
        elif isinstance(type(obj), type):
            # if obj has no builtin size and has additional pointers
            # if obj has builtin size, all the additional memory space is already added
            if not hasattr(obj, "__sizeof__") and hasattr(obj, "__dict__"):
                for k, v in getattr(obj, "__dict__").items():
                    total_size = total_size + _get_memory_size(k, False, visited)
                    total_size = total_size + _get_memory_size(v, False, visited)
        else:
            raise NotImplementedError("Not handled", obj)
    return total_size


def profile_variable_size(data: Any) -> float:
    """
    Compute the estimated total size of a variable.
    """
    if not _is_picklable(data):
        return float("inf")

    return float(_get_memory_size(data, True, set()))
