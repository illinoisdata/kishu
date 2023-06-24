from change.idgraph import IDGraph
import json

# (1) These tests verify id graph generation for individual object types.

def test_IDGraph_int():
    '''
    Test if idgraph can be created for a simple int.
    '''
    myint = 5
    id_graph = IDGraph(myint)

    expected_id = id(myint)
    actual_id = id_graph.get_obj_id()

    assert expected_id == actual_id


def test_compare_ints():
    '''
        Test if two ints can be accurately compared
    '''
    int1 = 5
    int2 = 5
    int3 = 6

    idgraph1 = IDGraph(int1)
    idgraph2 = IDGraph(int2)
    idgraph3 = IDGraph(int3)

    # Assert that two ints of same value are accurately compared
    assert idgraph1.compare(idgraph2) == True

    # Assert that two ints of different values are accuratelt compared
    assert idgraph1.compare(idgraph3) == False


def test_IDGraph_list():
    """
        Test if idgraph (json rep) is accurately generated for a list
    """
    # Init a list
    list1 = [1, 2, 3]
    # Get its memory addrtess
    expected_id = id(list1)
    expected_type = "list"

    idGraph1 = IDGraph(list1)
    idGraph1_json = json.loads(idGraph1.get_json())

    actual_id = idGraph1_json["obj_id"]
    actual_type = idGraph1_json["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    obj = {
        'obj_id': expected_id,
        'obj_type': 'list',
        'children': [
            {'obj_val': '3', 'obj_type': 'int', 'children': []},
            {'obj_val': '2', 'obj_type': 'int', 'children': []},
            {'obj_val': '1', 'obj_type': 'int', 'children': []}
        ]
    }
    expected_id_graph = json.dumps(obj)
    actual_id_graph = json.dumps(json.loads(str(idGraph1)))
    assert expected_id_graph == actual_id_graph

    idGraph2 = IDGraph(list1)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1.compare(idGraph2) == True

    list2 = [3, 4, 5]
    # Updating list1
    list1[2] = list2
    idGraph3 = IDGraph(list1)
    
    # ID Graph is a snapshot; the changes to the orignal do not alter already-generated ones
    assert idGraph1.compare(idGraph2) == True
    assert idGraph1.compare(idGraph3) == False
    

def test_compare_lists():
    """
        Test if two lists (different objects) are accurately compared
    """

    # Init first list
    list1 = [1,2,3]

    #Init second list
    list2 = [1,2,3]

    idgraph1 = IDGraph(list1)
    idgraph2 = IDGraph(list2)

    # Assert that comparison between different objects should return False
    assert idgraph1.compare(idgraph2) == False

    # Init third list
    list3 = [2,3,4]
    idgraph3 = IDGraph(list3)

    # Assert that comparison between different objects should return False
    assert idgraph1.compare(idgraph3) == False
    

def test_IDGraph_tuple():
    """
        Test if idgraph (json rep) is accurately generated for a Tuple
    """
    # Init a tuple
    tuple1 = (1, 2, 3.458)
    # Get its memory addrtess
    expected_id = id(tuple1)
    expected_type = "tuple"

    idGraph1 = IDGraph(tuple1)
    idGraph1_json = json.loads(idGraph1.get_json())
    actual_id = idGraph1_json["obj_id"]
    actual_type = idGraph1_json["obj_type"]

    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    obj = {
        'obj_id': expected_id,
        'obj_type': expected_type,
        'children': [
            {'obj_val': '3.458000', 'obj_type': 'float', 'children': []},
            {'obj_val': '2', 'obj_type': 'int', 'children': []},
            {'obj_val': '1', 'obj_type': 'int', 'children': []}
        ]
    }
    expected_id_graph = json.dumps(obj)
    actual_id_graph = json.dumps(json.loads(str(idGraph1)))
    assert expected_id_graph == actual_id_graph

    idGraph2 = IDGraph(tuple1)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1.compare(idGraph2) == True


def test_IDGraph_set():
    """
        Test if idgraph (json rep) is accurately generated for a set
    """
    # Init a set
    set1 = {"a", "b", 2, True, "c"}
    # Get its memory addrtess
    expected_id = id(set1)
    expected_type = "set"

    idGraph1 = IDGraph(set1)
    idGraph1_json = json.loads(idGraph1.get_json())
    actual_id = idGraph1_json["obj_id"]
    actual_type = idGraph1_json["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    idGraph2 = IDGraph(set1)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1.compare(idGraph2) == True, f"{idGraph1.get_json()}; {idGraph2.get_json()}"


def test_compare_sets():
    """
        Test if idgraphs of two sets with same elements in different order can be accurately compared
    """
    # Init the first set
    set1 = {1,2,3}

    # Init the second set
    set2 = {1,2,3}

    idgraph1 = IDGraph(set1)
    idgraph2 = IDGraph(set2)
    
    # Assert that comparison between different objects should return False
    assert idgraph1.compare(idgraph2) == False

    set1.clear()
    set1.add(1)
    set1.add(2)
    set1.add(3)

    # Assert that object remains same if values are cleared and re-added 
    assert idgraph1.compare(IDGraph(set1)) == True


def test_IDGraph_dictionary():
    """
        Test if idgraph (json rep) is accurately generated for a dictionary
    """
    # Init a dictionary
    dict1 = {1:"UIUC", 2:"DAIS"}
    # Get its memory addrtess
    expected_id =  id(dict1)
    expected_type = "dict"

    idGraph1 = IDGraph(dict1)
    idGraph1_json = json.loads(idGraph1.get_json())
    actual_id = idGraph1_json["obj_id"]
    actual_type = idGraph1_json["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    obj = {
        'obj_id': expected_id,
        'obj_type': expected_type,
        'children': [
            {'obj_val': 'DAIS', 'obj_type': 'string', 'children': []},
            {'obj_val': '2', 'obj_type': 'int', 'children': []},
            {'obj_val': 'UIUC', 'obj_type': 'string', 'children': []},
            {'obj_val': '1', 'obj_type': 'int', 'children': []}
        ]
    }
    expected_id_graph = json.dumps(obj)
    actual_id_graph = json.dumps(json.loads(str(idGraph1)))
    assert expected_id_graph == actual_id_graph

    idGraph2 = IDGraph(dict1)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1.compare(idGraph2) == True


def test_IDGraph_class_instance():
    """
        Test if idgraph (json rep) is accurately generated for a class instance
    """
    # Define a class
    class test:

        def __init__(self):
            self.my_int = 1
            self.my_bool = False
        
    # Init a class
    test1 = test()
    # Get its memory addrtess
    expected_id =  id(test1)
    expected_type = "class"

    idGraph1 = IDGraph(test1)
    idGraph1_json = json.loads(idGraph1.get_json())
    actual_id = idGraph1_json["obj_id"]
    actual_type = idGraph1_json["obj_type"]
    # Assert that the id and object type are as expected.
    assert expected_id == actual_id
    assert expected_type == actual_type

    obj = {
        'obj_id': expected_id,
        'obj_type': expected_type,
        'children': [
            {'obj_val': '0', 'obj_type': 'bool', 'children': []},
            {'obj_val': 'my_bool', 'obj_type': 'string', 'children': []},
            {'obj_val': '1', 'obj_type': 'int', 'children': []},
            {'obj_val': 'my_int', 'obj_type': 'string', 'children': []},
        ]
    }
    expected_id_graph = json.dumps(obj)
    actual_id_graph = json.dumps(json.loads(str(idGraph1)))
    print(actual_id_graph)
    assert expected_id_graph == actual_id_graph

    idGraph2 = IDGraph(test1)
    # Assert that the id graph does not change when the object remains unchanges
    assert idGraph1.compare(idGraph2) == True


def test_IDGraph_pandas_series():
    """
        Test if idgraph (json rep) is accurately generated for panda series
    """

    import numpy as np
    import pandas as pd

    s1 = pd.Series([1,2,3,4])

    idGraph1 = IDGraph(s1)
    idGraph1_json = json.loads(idGraph1.get_json())

    expected_type = "class"
    expected_id = id(s1)

    # Assert that the id and object type are as expected
    assert idGraph1_json["obj_id"] == expected_id
    assert idGraph1_json["obj_type"] == expected_type

    idGraph2 = IDGraph(s1)
    # Assert that the id graph does not change when the object remains unchanged
    assert idGraph1.compare(idGraph2) == True

    s1[2] = 0

    idGraph3 = IDGraph(s1)
    # Assert that the id graph changes when the object changes
    assert idGraph1.compare(idGraph3) == False

    s1[2] = 3
    s1[4] = 5

    idGraph4 = IDGraph(s1)
    # Assert that the id graph changes when object changes
    assert idGraph1.compare(idGraph4) == False


def test_IDGraph_pandas_df():
    """
        Test if idgraph (json rep) is accurately generated for pandas dataframe
    """
    import pandas as pd
    import numpy as np
    
    # Init a dataframe
    df = pd.DataFrame(np.array([[1,2,3],[4,5,6],[7,8,9]]), columns = ['a','b','c'])

    idGraph1 = IDGraph(df)
    idGraph1_json = json.loads(idGraph1.get_json())
    
    expected_type = "class"
    expected_id = id(df)
    # Assert that the id and object type are as expected
    assert idGraph1_json["obj_id"] == expected_id
    assert idGraph1_json["obj_type"] == expected_type
    
    idGraph2 = IDGraph(df)
    # Assert that the id graph does not change when the object remains unchanged
    assert idGraph1.compare(idGraph2) == True

    df.at[0,'a'] = 20

    idGraph3 = IDGraph(df)
    # Assert that the idgraph changes when the object changes
    assert idGraph1.compare(idGraph3) == False

    df.at[0,'a'] = 1
    new_row = {'a': 10, 'b': 11, 'c': 12}
    df.loc[len(df)] = new_row
    
    idGraph3 = IDGraph(df)
    # Assert that the id graph changes when the object changes (new row)
    assert idGraph1.compare(idGraph3) == False

    # Init a dataframe
    df2 = pd.DataFrame(np.array([[1,2,3],[4,5,6],[7,8,9]]), columns = ['a','b','c'])

    idGraph4 = IDGraph(df2)

    new_column  = [10,11,12]
    df2['d'] = new_column

    idGraph5 = IDGraph(df2)
    # Assert that the id graph changes when the object changes (new column)
    assert idGraph4.compare(idGraph5) == False

    df.drop(df.index, inplace=True)

    new_row = {'a': 1, 'b': 2, 'c': 3}     
    df.loc[len(df)] = new_row
    new_row = {'a': 4, 'b': 5, 'c': 6}  
    df.loc[len(df)] = new_row
    new_row = {'a': 7, 'b': 8, 'c': 9}  
    df.loc[len(df)] = new_row

    idGraph4 = IDGraph(df)
    # Assert that the igraph changes after dropping and re-adding values sinces pandas df are size-immutable
    assert idGraph1.compare(idGraph4) == False
    
    
def test_IDGraph_seaborn_displot():
    """
        Test if idgraph (json rep) is accurately generated for seaborn distribution plots
    """

    # Importing required libraries
    import pandas as pd
    import seaborn as sns

    # Init a df
    df = sns.load_dataset("penguins")
    
    # Generating a distribution plot object
    plot1 = sns.displot(data = df, x = "flipper_length_mm")

    idGraph1 = IDGraph(plot1)
    idGraph1_json = json.loads(idGraph1.get_json())

    expected_id = id(plot1)
    expected_type = "class"

    # Assert that id and object type are as expected
    assert idGraph1_json["obj_id"] == expected_id
    assert idGraph1_json["obj_type"] == expected_type

    idGraph2 = IDGraph(plot1)
    # Assert that the id graph does not change when the object remains unchanged
    assert idGraph1.compare(idGraph2) == True

    plot1.set(xlabel = 'flip_length')

    idGraph3 = IDGraph(plot1)
    # Assert that changing axes names changes idgraph of object
    assert idGraph1.compare(idGraph3) == False

    plot1.set(xlabel = 'flipper_length_mm')

    idGraph4 = IDGraph(plot1)
    # Assert that changing axes name back to original reverts back to original object
    assert idGraph1.compare(idGraph4) == True

    # Generating a distribution plot object
    plot2 = sns.displot(data = df, x = "flipper_length_mm")

    idGraph5 = IDGraph(plot2)

    plot2.set(title = 'Flipper Dis Plot')
    idGraph6 = IDGraph(plot2)
    # Assert that changing plot title changes idgraph of object
    assert idGraph5.compare(idGraph6) == False


def test_IDGraph_seaborn_scatterplot():
    """
        Test if idgraph (json rep) is accurately generated for seaborn scatter plots
    """

    # Importing required libraries
    import pandas as pd
    import seaborn as sns

    # Init a df
    df = sns.load_dataset("penguins")
    
    # Generating a scatter plot object
    plot1 = sns.scatterplot(data = df, x = "flipper_length_mm", y = "bill_length_mm")

    idGraph1 = IDGraph(plot1)
    idGraph1_json = json.loads(idGraph1.get_json())

    expected_id = id(plot1)
    expected_type = "class"

    # Assert that id and object type are as expected
    assert idGraph1_json["obj_id"] == expected_id
    assert idGraph1_json["obj_type"] == expected_type

    idGraph2 = IDGraph(plot1)
    # Assert that the id graph does not change when the object remains unchanged
    assert idGraph1.compare(idGraph2) == True

    plot1.set_xlabel('Flipper Length')

    idGraph3 = IDGraph(plot1)
    # Assert that changing axes names changes idgraph of object
    assert idGraph1.compare(idGraph3) == False

    plot1.set_xlabel('flipper_length_mm')

    idGraph4 = IDGraph(plot1)
    # Assert that changing axes name back to original reverts back to original object
    assert idGraph1.compare(idGraph4) == True

    # Generating a scatter plot object
    plot2 = sns.scatterplot(data = df, x = "flipper_length_mm", y = "bill_length_mm")

    idGraph5 = IDGraph(plot2)
    plot2.set_title("Flipper length vs Bill Length")
    idGraph6 = IDGraph(plot2)
    # Assert that changing plot title changes idgraph of object
    assert idGraph5.compare(idGraph6) == False


def test_IDGraph_seaborn_barplot():
    """
        Test if idgraph (json rep) is accurately generated for seaborn bar plots
    """

    # Importing required libraries
    import pandas as pd
    import seaborn as sns

    # Init a df
    df = sns.load_dataset("penguins")
    
    # Generating a bar plot object
    plot1 = sns.barplot(data = df, x = "island", y = "body_mass_g")

    idGraph1 = IDGraph(plot1)
    idGraph1_json = json.loads(idGraph1.get_json())

    expected_id = id(plot1)
    expected_type = "class"

    # Assert that id and object type are as expected
    assert idGraph1_json["obj_id"] == expected_id
    assert idGraph1_json["obj_type"] == expected_type

    idGraph2 = IDGraph(plot1)
    # Assert that the id graph does not change when the object remains unchanged
    assert idGraph1.compare(idGraph2) == True

    plot1.set_xlabel('Name of Island')

    idGraph3 = IDGraph(plot1)
    # Assert that changing axes name changes idgraph of object
    assert idGraph1.compare(idGraph3) == False

    plot1.set_xlabel('island')

    idGraph4 = IDGraph(plot1)
    # Assert that changing axes name back to original reverts back to original object
    assert idGraph1.compare(idGraph4) == True

    # Generating a bar plot object
    plot2 = sns.barplot(data = df, x = "island", y = "body_mass_g")

    idGraph5 = IDGraph(plot2)
    plot2.set_title("Island vs Body Mass")
    idGraph6 = IDGraph(plot2)
    # Assert that changing plot title changes idgraph of object
    assert idGraph5.compare(idGraph6) == False


def test_IDGraph_matplotlib_AxesSubplot():
    """
        Test if idgraph (json rep) is accurately generated for matplotlib AxesSubplot objects
    """

    import matplotlib.pyplot as plt

    # Init matplotlib figure and AxesSubplot objects
    fig, ax = plt.subplots(figsize=(2, 2), facecolor='lightskyblue', layout='constrained')

    idGraph1 = IDGraph(ax)
    idGraph1_json = json.loads(idGraph1.get_json())

    expected_id = id(ax)
    expected_type = "class"

    # Assert that id and object type are as expected
    assert idGraph1_json["obj_id"] == expected_id
    assert idGraph1_json["obj_type"] == expected_type

    idGraph2 = IDGraph(ax)
    # Assert that the id graph does not change when the object remains unchanged
    assert idGraph1.compare(idGraph2) == True

    ax.set_title('Axes', loc='left', fontstyle='oblique', fontsize='medium')

    idGraph3 = IDGraph(ax)
    # Assert that the idgraph changes when title is added to AxesSubplot
    assert idGraph1.compare(idGraph3) == False

    ax.set_xlabel("X-axis")

    idGraph4 = IDGraph(ax)
    # Assert that the idgraph changes when x-axis label is modified
    assert idGraph3.compare(idGraph4) == False


def test_IDGraph_matplotlib_Figure():
    """
        Test if idgraph (json rep) is accurately generated for matplotlib Figure objects
    """

    import matplotlib.pyplot as plt

    # Init a matplotlib Figure object
    fig = plt.figure(figsize=(2, 2), facecolor='lightskyblue', layout='constrained')

    idGraph1 = IDGraph(fig)
    idGraph1_json = json.loads(idGraph1.get_json())

    expected_id = id(fig)
    expected_type = "class"

    # Assert that id and object type are as expected
    assert idGraph1_json["obj_id"] == expected_id
    assert idGraph1_json["obj_type"] == expected_type

    idGraph2 = IDGraph(fig)
    # Assert that the id graph does not change when the object remains unchanged
    assert idGraph1.compare(idGraph2) == True

    fig.set_facecolor("green")

    idGraph3 = IDGraph(fig)
    # Assert that the idgraph changes when figure face color is modified
    assert idGraph1.compare(idGraph3) == False

    fig.set_facecolor("lightskyblue")

    idGraph4 = IDGraph(fig)
    # Assert that the idgraph reverts back to original when original face color is restored
    assert idGraph1.compare(idGraph4) == True

    fig.suptitle('Figure')

    idGraph5 = IDGraph(fig)
    # Assert that the idgraph changes when figure title is changed
    assert idGraph1.compare(idGraph5) == False

    figL, figR = fig.subfigures(1, 2)

    idGraph6 = IDGraph(fig)
    # Assert that the idgraph changes when subfigures are added to figure
    assert idGraph5.compare(idGraph6) == False

    figL.set_facecolor('thistle')

    idGraph7 = IDGraph(fig)
    # Assert that the idgraph changes when subfigure color is modified
    assert idGraph6.compare(idGraph7) == False

    ax = fig.add_subplot()

    idGraph8 = IDGraph(fig)
    # Assert that the idgraph changes when subplot is added
    assert idGraph7.compare(idGraph8) == False
    

# (2) These tests verify id graph generation for NESTED objects.
def test_create_idgraph_nested_list():
    """
        Test if idgraph (json rep) is accurately generated for a NESTED list
    """
    set1 = {"UIUC"}
    expected_set_id = id(set1)
    tuple1 = ("DAIS", "ELASTIC")
    expected_tup_id = id(tuple1)
    dict1 = {1:"a", 2:"b"}
    expected_dict_id = id(dict1)
    list1 = [set1, tuple1, dict1]
    expected_list_id = id(list1)

    idGraph1 = IDGraph(list1)
    idGraph1_json = json.loads(idGraph1.get_json())
    actual_list_id = idGraph1.get_obj_id()
    actual_set_id = 0
    actual_tup_id = 0
    actual_dict_id = 0
    for child in idGraph1_json["children"]:
        if child["obj_type"] == "set":
            actual_set_id = child['obj_id']
        if child["obj_type"] == "tuple":
            actual_tup_id = child['obj_id']
        if child["obj_type"] == "dict":
            actual_dict_id = child['obj_id']
    
    assert expected_list_id == actual_list_id
    assert expected_tup_id == actual_tup_id
    assert expected_set_id == actual_set_id
    assert expected_dict_id == actual_dict_id

    idGraph2 = IDGraph(list1)
    assert idGraph1.compare(idGraph2) == True

def test_create_idgraph_change_in_nested_dictionary():
    """
        Test if idgraph (json rep) is accurately generated for a NESTED dictionary
    """
    tuple1 = ("DAIS", "ELASTIC")
    expected_tup_id = id(tuple1)
    list1 = [1, 2, 3]
    expected_list_id = id(list1)
    dict1 = {tuple1:"a", 2:list1}
    expected_dict_id = id(dict1)

    idGraph1 = IDGraph(dict1)
    idGraph1_json = json.loads(idGraph1.get_json())
    actual_dict_id = idGraph1.get_obj_id()
    actual_tup_id = 0
    actual_list_id = 0

    for child in idGraph1_json["children"]:
        if child["obj_type"] == "tuple":
            actual_tup_id = child["obj_id"]
        if child["obj_type"] == "list":
            actual_list_id = child["obj_id"]
    
    assert expected_dict_id == actual_dict_id
    assert expected_tup_id == actual_tup_id
    assert expected_list_id == actual_list_id

    idGraph2 = IDGraph(dict1)
    assert idGraph1.compare(idGraph2) == True

# (3) These tests verify id graph generation for CYCLIC objects.
def test_create_idgraph_change_in_cyclic_dictionary():
    """
        Test if idgraph (json rep) is accurately generated for a CYCLIC dictionary
    """
    set1 = {"DAIS", "ELASTIC"}
    expected_set_id = id(set1)
    list1 = [1, 2, 3]
    expected_list_id = id(list1)
    dict1 = {1:set1, 2:list1}
    expected_dict_id = id(dict1)
    list1[2] = dict1

    idGraph1 = IDGraph(dict1)
    idGraph1_json = json.loads(idGraph1.get_json())

    actual_dict_id = idGraph1.get_obj_id()
    actual_set_id = 0
    actual_list_id = 0
    actual_dict_cycle_id = 0

    for child in idGraph1_json["children"]:
        if child["obj_type"] == "set":
            actual_set_id = child["obj_id"]
        if child["obj_type"] == "list":
            actual_list_id = child["obj_id"]
            actual_dict_cycle_id = child["children"][0]["obj_id"]
    
    assert expected_dict_id == actual_dict_id
    assert expected_dict_id == actual_dict_cycle_id
    assert expected_set_id == actual_set_id
    assert expected_list_id == actual_list_id
