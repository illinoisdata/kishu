import dill
import inspect
import pickle
import sys
import types

from typing import Any, Optional

from kishu.storage.config import Config


def _get_object_module(obj: Any) -> Optional[str]:
    """
        Get the name of the module an object is from.
    """
    obj_module_full = getattr(obj, "__module__", None)
    return obj_module_full.split(".")[0] if isinstance(obj_module_full, str) else None


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
        if not is_picklable and Config.get_config_entry('PROFILER', 'auto_add_unpicklable_object', False):
            unserializable_list = Config.get_config_entry('PROFILER', 'excluded_modules', [])
            unserializable_list.append(_get_object_module(obj))
            Config.set_config_entry('PROFILER', 'excluded_modules', str(unserializable_list))
        return is_picklable
    except Exception:
        pass

    # Double check with pickle library, which is slower but more robust.
    # TODO: remove this in the future, returning false when Dill fails.
    try:
        pickle.dumps(obj)
    except Exception:
        # Add the unpicklable object to the config file.
        if Config.get_config_entry('PROFILER', 'auto_add_unpicklable_object', False):
            unserializable_list = Config.get_config_entry('PROFILER', 'excluded_modules', [])
            unserializable_list.append(_get_object_module(obj))
            Config.set_config_entry('PROFILER', 'excluded_modules', unserializable_list)
        return False
    return True


def _in_exclude_list(obj: Any) -> bool:
    """
        Checks whether object is from a class which Dill reports is pickleable but is actually not.
    """
    # TODO: remove 'qiskit' from default once recomptuation works.
    return _get_object_module(obj) in Config.get_config_entry('PROFILER', 'excluded_modules', ["qiskit"])


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
        elif obj_type in [types.FunctionType, types.MethodType, types.BuiltinFunctionType, types.ModuleType] \
                or isinstance(obj, type):  # True if obj is a class
            pass
        # custom class instance
        elif isinstance(type(obj), type):
            # if obj has no builtin size and has additional pointers
            # if obj has builtin size, all the additional memory space is already added
            if not hasattr(obj, "__sizeof__") and hasattr(obj, "__dict__"):
                for (k, v) in getattr(obj, "__dict__").items():
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
        return float('inf')

    return float(_get_memory_size(data, True, set()))
