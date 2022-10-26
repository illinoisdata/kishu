import unittest
import numpy as np
import pandas as pd
import pickle

from elastic.core.io.pickle import is_picklable


class TestPickle(unittest.TestCase):
    def test_is_picklable_numpy(self):
        arr = np.array([1, 2, 3])
        self.assertTrue(is_picklable(arr))
        
        arr_pickled = pickle.dumps(arr)
        arr_recovered = pickle.loads(arr_pickled)
        self.assertTrue(isinstance(arr_recovered, np.ndarray))
        self.assertTrue(np.alltrue(arr == arr_recovered))
        
    def test_is_picklable_pandas(self):
        df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                          columns=['a', 'b', 'c'])
        self.assertTrue(is_picklable(df))
        
        df_pickled = pickle.dumps(df)
        df_recovered = pickle.loads(df_pickled)
        self.assertTrue(isinstance(df_recovered, pd.DataFrame))
        self.assertTrue(df_recovered.equals(df))


if __name__ == '__main__':
    unittest.main()
