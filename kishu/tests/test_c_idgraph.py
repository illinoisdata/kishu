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

    def test_create_idgraph_change_in_list(self):
        """
            Test if the C module can consistently return idgraph (string rep) for an unchanged list
        """
        profile_dict = {}

        list1 = [1,2,3]
        list2 = ["string",list1]
        idGraph1 = construct_fingerprint(list2,profile_dict)
        list2[1] = 0
        idGraph2 = construct_fingerprint(list2,profile_dict)
        list2[1] = list1
        idGraph3 = construct_fingerprint(list2,profile_dict)

        self.assertNotEqual(idGraph1,idGraph2)
        self.assertEqual(idGraph1,idGraph3)
        self.assertNotEqual(idGraph2,idGraph3)


if __name__ == '__main__':
    unittest.main()