import os, sys, time
import numpy as np
import pickle
import types


def profile_variable_size(data):
    """
        Compute the estimated total size of a variable.
    """
    def get_memory_size(obj, is_initialize, visited):
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
                    total_size = total_size + get_memory_size(e, False, visited)
            elif obj_type is dict:
                for k, v in obj.items():
                    total_size = total_size + get_memory_size(k, False, visited)
                    total_size = total_size + get_memory_size(v, False, visited)
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
                        total_size = total_size + get_memory_size(k, False, visited)
                        total_size = total_size + get_memory_size(v, False, visited)
            else:
                raise NotImplementedError("Not handled", obj)
        return total_size

    return get_memory_size(data, True, set())


def profile_migration_speed(dirname: str, alpha=1) -> float:
    """
        The migration speed is the sum of read and write speed (since we are writing the state to disk, then
        reading from disk to restore the notebook). The function should ideally be fast (<1 sec).
        Args:
            dirname: Location to profile.
    """
    filecount = 1
    max_time = 0.8
    testing_dir = os.path.join(dirname, "measure_speed")
    os.system("rm -rf {} && mkdir {}".format(testing_dir, testing_dir))
    total_bytes = 0

    start_time = time.time()

    total_read_time = 0
    total_write_time = 0
    for i in range(filecount):
        write_array_large = np.random.rand(1000, 1000)
        write_array_small = np.random.rand(10, 10)
        total_bytes += sys.getsizeof(write_array_large)
        total_bytes -= sys.getsizeof(write_array_small)

        write_start = time.time()
        out_file = open(os.path.join(testing_dir, str(i) + "large"), "wb")
        pickle.dump(write_array_large, out_file)
        out_file.close()
        total_write_time += time.time() - write_start

        read_start = time.time()
        in_file = open(os.path.join(testing_dir, str(i)) + "large", "rb")
        in_file.close()
        total_read_time += time.time() - read_start

        write_start = time.time()
        out_file = open(os.path.join(testing_dir, str(i) + "small"), "wb")
        pickle.dump(write_array_small, out_file)
        out_file.close()
        total_write_time -= time.time() - write_start

        read_start = time.time()
        in_file = open(os.path.join(testing_dir, str(i) + "small"), "rb")
        in_file.close()
        total_read_time -= time.time() - read_start


        if time.time() - start_time > max_time:
            break

    os.system("rm -rf {}".format(testing_dir))

    migration_speed_bps = total_bytes / (total_read_time + total_write_time * alpha)
    return migration_speed_bps
