from change.c_idgraph import construct_fingerprint

# (1) These tests verify id graph generation for individual object types.
def test_construct_fingerprint_list():
    """
        Test if idgraph (json rep) is accurately generated for a list
    """
    # Init a list
    list1 = [1,2,3]
    # Get its memory addrtess
    expected_id = format(id(list1), 'x')
    expected_type = "list"

    profile_dict = {}
    idGraph1 = construct_fingerprint(list1,profile_dict)
    actual_id = format(int(idGraph1["obj_id"],16),"x")
    actual_type = idGraph1["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    idGraph2 = construct_fingerprint(list1,profile_dict)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1 == idGraph2

    list2 = [3,4,5]
    # Updating list1
    list1[2] = list2
    idGraph3 = construct_fingerprint(list1,profile_dict)
    # Assert that the id graph changes when the object itself is updated.
    assert idGraph1 == idGraph2 != idGraph3
    
def test_construct_fingerprint_tuple():
    """
        Test if idgraph (json rep) is accurately generated for a Tuple
    """
    # Init a tuple
    tuple1 = (1,2,3)
    # Get its memory addrtess
    expected_id = format(id(tuple1), 'x')
    expected_type = "tuple"

    profile_dict = {}
    idGraph1 = construct_fingerprint(tuple1,profile_dict)
    actual_id = format(int(idGraph1["obj_id"],16),"x")
    actual_type = idGraph1["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    idGraph2 = construct_fingerprint(tuple1,profile_dict)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1 == idGraph2

def test_construct_fingerprint_set():
    """
        Test if idgraph (json rep) is accurately generated for a set
    """
    # Init a set
    set1 = {"a","b",2,3,"c"}
    # Get its memory addrtess
    expected_id = format(id(set1), 'x')
    expected_type = "set"

    profile_dict = {}
    idGraph1 = construct_fingerprint(set1,profile_dict)
    actual_id = format(int(idGraph1["obj_id"],16),"x")
    actual_type = idGraph1["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    idGraph2 = construct_fingerprint(set1,profile_dict)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1 == idGraph2

def test_construct_fingerprint_dictionary():
    """
        Test if idgraph (json rep) is accurately generated for a dictionary
    """
    # Init a dictionary
    dict1 = {1:"UIUC", 2:"DAIS"}
    # Get its memory addrtess
    expected_id =  format(id(dict1), 'x')
    expected_type = "dictionary"

    profile_dict = {}
    idGraph1 = construct_fingerprint(dict1,profile_dict)
    actual_id = format(int(idGraph1["obj_id"],16),"x")
    actual_type = idGraph1["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    idGraph2 = construct_fingerprint(dict1,profile_dict)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1 == idGraph2

def test_construct_fingerprint_class_instance():
    """
        Test if idgraph (json rep) is accurately generated for a class instance
    """
    # Define a class
    class test:
        a = 1
    
    # Init a class
    test1 = test()
    # Get its memory addrtess
    expected_id =  format(id(test1), 'x')
    expected_type = "class object"

    profile_dict = {}
    idGraph1 = construct_fingerprint(test1,profile_dict)
    actual_id = format(int(idGraph1["obj_id"],16),"x")
    actual_type = idGraph1["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    idGraph2 = construct_fingerprint(test1,profile_dict)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1 == idGraph2


# (2) These tests verify id graph generation for NESTED objects.
def test_create_idgraph_nested_list():
    """
        Test if idgraph (json rep) is accurately generated for a NESTED list
    """
    set1 = {"UIUC"}
    expected_set_id =  format(id(set1), 'x')
    tuple1 = ("DAIS","ELASTIC")
    expected_tup_id =  format(id(tuple1), 'x')
    dict1 = {1:"a",2:"b"}
    expected_dict_id = format(id(dict1), 'x')
    list1 = [set1,tuple1,dict1]
    expected_list_id = format(id(list1), 'x')
    profile_dict = {}

    idGraph1 = construct_fingerprint(list1,profile_dict)
    actual_list_id = format(int(idGraph1["obj_id"],16),"x")
    actual_set_id = 0
    actual_tup_id = 0
    actual_dict_id = 0
    for child in idGraph1["children"]:
        if child["obj_type"] == "set":
            actual_set_id = format(int(child["obj_id"],16),"x")
        if child["obj_type"] == "tuple":
            actual_tup_id = format(int(child["obj_id"],16),"x")
        if child["obj_type"] == "dictionary":
            actual_dict_id = format(int(child["obj_id"],16),"x")
    
    assert expected_list_id == actual_list_id
    assert expected_tup_id == actual_tup_id
    assert expected_set_id == actual_set_id
    assert expected_dict_id == actual_dict_id

    idGraph2 = construct_fingerprint(list1,profile_dict)
    assert idGraph1 == idGraph2

def test_create_idgraph_change_in_nested_dictionary():
    """
        Test if idgraph (json rep) is accurately generated for a NESTED dictionary
    """
    tuple1 = ("DAIS","ELASTIC")
    expected_tup_id = format(id(tuple1), 'x')
    list1 = [1,2,3]
    expected_list_id = format(id(list1), 'x')
    dict1 = {tuple1:"a",2:list1}
    expected_dict_id = format(id(dict1), 'x')
    profile_dict = {}

    idGraph1 = construct_fingerprint(dict1,profile_dict)
    actual_dict_id = format(int(idGraph1["obj_id"],16),"x")
    actual_tup_id = 0
    actual_list_id = 0

    for child in idGraph1["children"]:
        if child["obj_type"] == "tuple":
            actual_tup_id = format(int(child["obj_id"],16),"x")
        if child["obj_type"] == "list":
            actual_list_id = format(int(child["obj_id"],16),"x")
    
    assert expected_dict_id == actual_dict_id
    assert expected_tup_id == actual_tup_id
    assert expected_list_id == actual_list_id

    idGraph2 = construct_fingerprint(dict1,profile_dict)
    assert idGraph1 == idGraph2

# (3) These tests verify id graph generation for CYCLIC objects.
def test_create_idgraph_change_in_cyclic_dictionary():
    """
        Test if idgraph (json rep) is accurately generated for a CYCLIC dictionary
    """
    set1 = {"DAIS","ELASTIC"}
    expected_set_id = format(id(set1), 'x')
    list1 = [1,2,3]
    expected_list_id = format(id(list1), 'x')
    dict1 = {1:set1,2:list1}
    expected_dict_id = format(id(dict1), 'x')
    list1[2] = dict1
    profile_dict = {}

    idGraph1 = construct_fingerprint(dict1,profile_dict)

    actual_dict_id = format(int(idGraph1["obj_id"],16),"x")
    actual_set_id = 0
    actual_list_id = 0
    actual_dict_cycle_id = 0

    for child in idGraph1["children"]:
        if child["obj_type"] == "set":
            actual_set_id = format(int(child["obj_id"],16),"x")
        if child["obj_type"] == "list":
            actual_list_id = format(int(child["obj_id"],16),"x")
            actual_dict_cycle_id = format(int(child["children"][0]["obj_id"],16),"x")
    
    assert expected_dict_id == actual_dict_id
    assert expected_dict_id == actual_dict_cycle_id
    assert expected_set_id == actual_set_id
    assert expected_list_id == actual_list_id