from kishu.planning import object_state
from kishu.planning import idgraph_visitor
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pickle


def test_idgraph_numpy():
    """
        Test if idgraph is accurately generated for numpy arrays
    """
    vis1 = idgraph_visitor.idgraph()
    a = np.arange(6)

    idgraph1 = object_state.create_idgraph(a)
    idgraph2 = object_state.create_idgraph(a)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(a)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    a[3] = 10
    idgraph3 = object_state.create_idgraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    a[3] = 3
    idgraph4 = object_state.create_idgraph(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4


def test_idgraph_pandas_Series():
    """
        Test if idgraph is accurately generated for panda series
    """
    vis1 = idgraph_visitor.idgraph()
    s1 = pd.Series([1, 2, 3, 4])

    idgraph1 = object_state.create_idgraph(s1)
    idgraph2 = object_state.create_idgraph(s1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(s1)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    s1[2] = 0

    idgraph3 = object_state.create_idgraph(s1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    s1[2] = 3

    idgraph4 = object_state.create_idgraph(s1)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4


def test_idgraph_pandas_df():
    """
        Test if idgraph is accurately generated for panda dataframes
    """
    vis1 = idgraph_visitor.idgraph()
    df = sns.load_dataset('penguins')

    idgraph1 = object_state.create_idgraph(df)
    idgraph2 = object_state.create_idgraph(df)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(df)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    df.at[0, 'species'] = "Changed"
    idgraph3 = object_state.create_idgraph(df)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    df.at[0, 'species'] = "Adelie"
    idgraph4 = object_state.create_idgraph(df)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4

    new_row = {'species': "New Species", 'island': "New island", 'bill_length_mm': 999,
               'bill_depth_mm': 999, 'flipper_length_mm': 999, 'body_mass_g': 999, 'sex': "Male"}
    df.loc[len(df)] = new_row

    idgraph5 = object_state.create_idgraph(df)

    # Assert that idgraph changes when new row is added to dataframe
    assert idgraph1 != idgraph5


def test_idgraph_matplotlib():
    """
        Test if idgraph is accurately generated for matplotlib objects
    """
    vis1 = idgraph_visitor.idgraph()
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    idgraph1 = object_state.create_idgraph(a)
    idgraph2 = object_state.create_idgraph(a)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(a) and idgraph1.children[0].id_obj == id(a[0])

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are the same
    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plt.xlabel("XLABEL_2")
    idgraph3 = object_state.create_idgraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plt.xlabel("XLABEL_1")
    idgraph4 = object_state.create_idgraph(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color('red')
    idgraph5 = object_state.create_idgraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    line.set_color(line_co)
    idgraph6 = object_state.create_idgraph(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph6
    else:
        assert idgraph1 == idgraph6

    # Close all figures
    plt.close('all')


def test_idgraph_seaborn_displot():
    """
        Test if idgraph is accurately generated for seaborn displot objects (figure-level object)
    """
    vis1 = idgraph_visitor.idgraph()
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    idgraph1 = object_state.create_idgraph(plot1)
    idgraph2 = object_state.create_idgraph(plot1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plot1.set(xlabel="NEW LABEL")
    idgraph3 = object_state.create_idgraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set(xlabel="flipper_length_mm")
    idgraph4 = object_state.create_idgraph(plot1)
    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    # Close all figures
    plt.close('all')


def test_idgraph_seaborn_scatterplot():
    """
        Test if idgraph is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    vis1 = idgraph_visitor.idgraph()

    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    idgraph1 = object_state.create_idgraph(plot1)
    idgraph2 = object_state.create_idgraph(plot1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plot1.set_xlabel('Flipper Length')
    idgraph3 = object_state.create_idgraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set_xlabel('flipper_length_mm')
    idgraph4 = object_state.create_idgraph(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    plot1.set_facecolor('#eafff5')
    idgraph5 = object_state.create_idgraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    # Close all figures
    plt.close('all')
