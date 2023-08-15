from kishu import idgraph2 as idgraph
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pickle


def test_idgraph_numpy():
    """
        Test if idgraph is accurately generated for numpy arrays
    """
    a = np.arange(6)

    idgraph1 = idgraph.get_object_state(a)
    idgraph2 = idgraph.get_object_state(a)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(a)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph.compare_idgraph(idgraph1, idgraph2) == True

    a[3] = 10
    idgraph3 = idgraph.get_object_state(a)

    # Assert that the id graph changes when the object changes
    assert idgraph.compare_idgraph(idgraph1, idgraph3) == False

    a[3] = 3
    idgraph4 = idgraph.get_object_state(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph.compare_idgraph(idgraph1, idgraph4) == True

def test_idgraph_pandas():
    # test_idgraph_pandas_Series()
    test_idgraph_pandas_df()


# def test_idgraph_pandas_Series():
#     """
#         Test if idgraph is accurately generated for panda series
#     """
#     s1 = pd.Series([1,2,3,4])

#     idgraph1 = idgraph.get_object_state(s1)
#     idgraph2 = idgraph.get_object_state(s1)

#     # Assert that the obj id is as expected
#     assert idgraph1.id_obj == id(s1)

#     # Assert that the id graph does not change when the object remains unchanged
#     assert idgraph.compare_idgraph(idgraph1, idgraph2) == True

#     s1[2] = 0

#     idgraph3 = idgraph.get_object_state(s1)

#     # Assert that the id graph changes when the object changes
#     assert idgraph.compare_idgraph(idgraph1, idgraph3) == False

#     s1[2] = 3

#     idgraph4 = idgraph.get_object_state(s1)

#     # Assert that the original id graph is restored when the original object state is restored
#     assert idgraph.compare_idgraph(idgraph1, idgraph4) == True

    
def test_idgraph_pandas_df():
    """
        Test if idgraph is accurately generated for panda dataframes
    """    
    df = sns.load_dataset('penguins')

    idgraph1 = idgraph.get_object_state(df)
    idgraph2 = idgraph.get_object_state(df)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(df)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph.compare_idgraph(idgraph1, idgraph2) == True
    
    df.at[0,'species'] = "Changed"
    idgraph3 = idgraph.get_object_state(df)

    # Assert that the id graph changes when the object changes
    assert idgraph.compare_idgraph(idgraph1, idgraph3) == False

    df.at[0,'species'] = "Adelie"
    idgraph4 = idgraph.get_object_state(df)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph.compare_idgraph(idgraph1, idgraph4) == True

    new_row = {'species': "New Species", 'island': "New island", 'bill_length_mm': 999, 'bill_depth_mm': 999, 'flipper_length_mm': 999, 'body_mass_g': 999, 'sex': "Male"}
    df.loc[len(df)] = new_row

    idgraph5 = idgraph.get_object_state(df)

    # Assert that idgraph changes when new row is added to dataframe
    assert idgraph.compare_idgraph(idgraph1, idgraph5) == False

def test_idgraph_matplotlib():
    """
        Test if idgraph is accurately generated for matplotlib objects
    """    
    df = pd.DataFrame(np.array([[1,2,3],[4,5,6],[7,8,9]]), columns = ['a','b','c'])
    a = plt.plot(df['a'],df['b'])
    plt.xlabel("XLABEL_1")

    idgraph1 = idgraph.get_object_state(a)
    idgraph2 = idgraph.get_object_state(a)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(a) and idgraph1.children[0].id_obj == id(a[0])

    # Assert that the id graph does not change when the object remains unchanged
    # assert idgraph.compare_idgraph(idgraph1, idgraph2) == True

    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    assert pick1 == pick2

    # ls1 = []
    # ls2 = []

    # idgraph.convert_idgraph_to_list(idgraph1, ls1)
    # idgraph.convert_idgraph_to_list(idgraph2, ls2)

    # assert ls1 == ls2

    plt.xlabel("XLABEL_2")
    idgraph3 = idgraph.get_object_state(a)

    # Assert that the id graph changes when the object changes
    assert idgraph.compare_idgraph(idgraph1, idgraph3) == False

    plt.xlabel("XLABEL_1")
    idgraph4 = idgraph.get_object_state(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph.compare_idgraph(idgraph1, idgraph4) == True

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color('red')
    idgraph5 = idgraph.get_object_state(a)

    # Assert that the id graph changes when the object changes
    assert idgraph.compare_idgraph(idgraph1, idgraph5) == False

    line.set_color(line_co)
    idgraph6 = idgraph.get_object_state(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph.compare_idgraph(idgraph1, idgraph6) == True

def test_idgraph_seaborn():
    test_idgraph_seaborn_displot()
    test_idgraph_seaborn_scatterplot()

def test_idgraph_seaborn_displot():
    """
        Test if idgraph is accurately generated for seaborn displot objects (figure-level object)
    """
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm", y="bill_length_mm", kind="kde")

    idgraph1 = idgraph.get_object_state(plot1)
    idgraph2 = idgraph.get_object_state(plot1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(plot1)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph.compare_idgraph(idgraph1, idgraph2) == True

    plot1.set(xlabel="NEW LABEL")
    idgraph3 = idgraph.get_object_state(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph.compare_idgraph(idgraph1, idgraph3) == False

    plot1.set(xlabel="flipper_length_mm")
    idgraph4 = idgraph.get_object_state(plot1)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph.compare_idgraph(idgraph1, idgraph4) == True

def test_idgraph_seaborn_scatterplot():
    """
        Test if idgraph is accurately generated for seaborn scatterplot objects (axes-level object)
    """

    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data = df, x = "flipper_length_mm", y = "bill_length_mm")

    idgraph1 = idgraph.get_object_state(plot1)
    idgraph2 = idgraph.get_object_state(plot1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(plot1)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph.compare_idgraph(idgraph1, idgraph2) == True

    plot1.set_xlabel('Flipper Length')
    idgraph3 = idgraph.get_object_state(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph.compare_idgraph(idgraph1, idgraph3) == False

    plot1.set_xlabel('flipper_length_mm')
    idgraph4 = idgraph.get_object_state(plot1)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph.compare_idgraph(idgraph1, idgraph4) == True

    plot1.set_facecolor('#eafff5')
    idgraph5 = idgraph.get_object_state(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph.compare_idgraph(idgraph1, idgraph5) == False













    
    



    












    