import dill
import inspect
import pickle
import sys
import types


def _is_picklable(obj) -> bool:
    """
        Checks whether an object is pickleable.
    """
    if _is_exception_class(obj):
        return False
    if inspect.ismodule(obj):
        return True
    try:
        # This function can crash.
        # TODO: add hardcoded pickable objects list for which dill fails on but is common (e.g., pandas dataframes)
        return dill.pickles(obj)
    except Exception:
        pass

    # Double check with pickle library, which is slower but more robust.
    # TODO: remove this in the future, returning false when Dill fails.
    try:
        pickle.dumps(obj)
    except Exception:
        return False
    return True


def _is_exception_class(obj) -> bool:
    """
        Checks whether object is from a class which Dill reports is pickleable but is actually not.
    """
    # TODO: replace this with a config file
    for class_name in ["qiskit"]:
        if inspect.getmodule(obj) and class_name in str(inspect.getmodule(obj)):
            return True
    return False


def _get_memory_size(obj, is_initialize: bool, visited: set) -> int:
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


def profile_variable_size(data) -> float:
    """
        Compute the estimated total size of a variable.
    """
    if not _is_picklable(data):
        return float('inf')

    return float(_get_memory_size(data, True, set()))
