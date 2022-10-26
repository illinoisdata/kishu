import unittest

import pandas as pd
from elastic.core.common.profile_variable_size import profile_variable_size
import sys


class TestProfileVariableSize(unittest.TestCase):
    def test_primitive_size(self):
        """
            Profiled size should equal size from sys.getsizeof for primitives and single-level data structures.
        """
        x = 1
        self.assertEqual(sys.getsizeof(x), profile_variable_size(x))

        y = [1, 2, 3]
        self.assertEqual(sys.getsizeof(y), profile_variable_size(y))

        # Some classes (i.e. dataframe) have built in __size__ function.
        z = pd.DataFrame([[1, 2], [3, 4], [5, 6]])
        self.assertEqual(sys.getsizeof(z), profile_variable_size(z))

    def test_nested_list_size(self):
        """
            Profile variable size should work correctly for nested lists.
        """
        x1 = [1, 2, 3, 4, 5]
        x2 = [6, 7, 8, 9, 10]
        y = [x1, x2]

        self.assertLessEqual(sys.getsizeof(x1) + sys.getsizeof(x2), profile_variable_size(y))

    def test_repeated_pointers(self):
        """
            Profile variable size should count each unique item only once.
        """
        x1 = [i for i in range(100)]
        y = [x1, x1, x1, x1, x1]

        self.assertGreaterEqual(sys.getsizeof(x1) * 5, profile_variable_size(y))

    def test_recursive_list_size(self):
        """
            This should terminate correctly.
        """
        a = []
        b = []
        a.append(b)
        b.append(a)

        self.assertLessEqual(0, profile_variable_size(a))


if __name__ == '__main__':
    unittest.main()
