import unittest
from change.c_idgraph import construct_fingerprint

class TestIdgraph(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_create_idgraph_simple_list(self):
        """
            Test if the C module can consistently return idgraph (string rep) for an unchanged list
        """
        list1 = [1,2,3]
        profile_dict = {}
        idGraph1 = construct_fingerprint(list1,profile_dict)
        idGraph2 = construct_fingerprint(list1,profile_dict)
        self.assertEqual(idGraph1,idGraph2)

    def test_create_idgraph_nested_list(self):
        """
            Test if the C module can consistently return idgraph (string rep) for an unchanged list
        """
        list1 = [1,2,3]
        list2 = ["string",list1]
        profile_dict = {}
        idGraph1 = construct_fingerprint(list2,profile_dict)
        idGraph2 = construct_fingerprint(list2,profile_dict)
        self.assertEqual(idGraph1,idGraph2)

if __name__ == '__main__':
    unittest.main()