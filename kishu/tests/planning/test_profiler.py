import sys
from pathlib import Path

import numpy as np
import pandas as pd

from kishu.planning.profiler import profile_variable_size
from kishu.storage.config import Config


def test_primitive_size():
    """
    Profiled size should equal size from sys.getsizeof for primitives and single-level data structures.
    """
    x = 1
    assert profile_variable_size(x) == sys.getsizeof(x)

    y = [1, 2, 3]
    assert profile_variable_size(y) == sys.getsizeof(y)

    # Some classes (i.e. dataframe) have built in __size__ function.
    z = pd.DataFrame([[1, 2], [3, 4], [5, 6]])
    assert profile_variable_size(z) == sys.getsizeof(z)


def test_nested_list_size():
    """
    Profile variable size should work correctly for nested lists.
    """
    x1 = [1, 2, 3, 4, 5]
    x2 = [6, 7, 8, 9, 10]
    y = [x1, x2]

    assert profile_variable_size(y) >= sys.getsizeof(x1) + sys.getsizeof(x2)


def test_repeated_pointers():
    """
    Profile variable size should count each unique item only once.
    """
    x1 = [i for i in range(100)]
    y = [x1, x1, x1, x1, x1]

    assert profile_variable_size(y) <= sys.getsizeof(x1) * 5


def test_recursive_list_size():
    """
    This should terminate correctly.
    """
    a = []
    b = []
    a.append(b)
    b.append(a)

    assert profile_variable_size(a) >= 0


def test_numpy_array():
    arr = np.array([1, 2, 3])
    assert profile_variable_size(arr) < np.inf


def test_pandas_dataframe():
    df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=["a", "b", "c"])
    assert profile_variable_size(df) < np.inf


def test_generator():
    gen = (i for i in range(10))
    assert profile_variable_size(gen) == np.inf


def test_add_unserializable_variable_to_config(tmp_path: Path):
    Config.set("PROFILER", "auto_add_unpicklable_object", True)
    assert Config.get("PROFILER", "auto_add_unpicklable_object", False)

    # Try profiling the size of a generator.
    # Its class will be added to the unserializable list in the config.
    gen = (i for i in range(10))
    assert profile_variable_size(gen) == np.inf

    # The generator has no module, so it is only added to the class list.
    assert Config.get("PROFILER", "excluded_modules", []) == []
    assert Config.get("PROFILER", "excluded_classes", []) == ["<class 'generator'>"]
