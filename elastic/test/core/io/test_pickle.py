import unittest
import numpy as np
import pandas as pd
import pickle
from datetime import datetime, date
from pyspark.sql import DataFrame, SparkSession

from elastic.core.io.pickle import is_picklable, _is_picklable_dill

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
    
    # FIXME: this unit test is currently much slower than others
    def test_is_picklable_pyspark(self):        
        session = SparkSession.builder.getOrCreate()
        
        rdd = session.sparkContext.parallelize([
            (1, 2., 'string1', date(2000, 1, 1), datetime(2000, 1, 1, 12, 0)),
            (2, 3., 'string2', date(2000, 2, 1), datetime(2000, 1, 2, 12, 0)),
            (3, 4., 'string3', date(2000, 3, 1), datetime(2000, 1, 3, 12, 0))
        ])
        df = session.createDataFrame(rdd, schema=['a', 'b', 'c', 'd', 'e'])
        self.assertFalse(is_picklable(df))
        
        # df_pickled = pickle.dumps(df)
        # df_recovered = pickle.loads(df_pickled)
        # self.assertTrue(isinstance(df_recovered, DataFrame))
        # self.assertEqual(df_recovered.schema, df.schema)
        # self.assertEqual(df_recovered.collect(), df.collect())
        
        session.stop()

if __name__ == '__main__':
    unittest.main()
