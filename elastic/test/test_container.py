import unittest

from container import DataContainer

class TestDataContainer(unittest.TestCase):
    def test_init(self):
        int1 = 1
        d1 = DataContainer(int1, prevOpEvent=None)
        self.assertEqual(d1.get_base_type(), int)
        self.assertEqual(d1.get_base_id(), id(int1))
        
        d1 = DataContainer(d1, prevOpEvent=None)
        self.assertEqual(d1.get_base_type(), int)
        self.assertEqual(d1.get_base_id(), id(int1))
        

if __name__ == '__main__':
    unittest.main()