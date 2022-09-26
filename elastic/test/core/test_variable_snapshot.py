import unittest

from core.notebook.variable_snapshot import VariableSnapshot

class TestVariableSnapshot(unittest.TestCase):
    def test_init(self):
        int1 = 1
        d1 = VariableSnapshot("int1", 1, int1, prevOpEvent=None)
        self.assertEqual(d1.get_base_type(), int)
        self.assertEqual(d1.get_base_id(), id(int1))
        self.assertEqual(d1.get_name(), "int1")
        self.assertEqual(d1.get_version(), 1)

if __name__ == '__main__':
    unittest.main()
