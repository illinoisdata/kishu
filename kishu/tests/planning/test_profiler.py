import pandas as pd
import sys

from kishu.planning.profiler import profile_variable_size


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
