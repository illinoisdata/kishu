import pickle

import numpy as np
import pandas as pd
import seaborn as sns

from kishu.planning import object_state


def test_idgraph_numpy():
    """
    Test if idgraph is accurately generated for numpy arrays
    """
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


def test_hash_numpy():
    """
    Test if hash is accurately generated for numpy arrays
    """
    a = np.arange(6)

    hash1 = object_state.create_hash(a)
    hash2 = object_state.create_hash(a)

    # Assert that the hash does not change when the object remains unchanged
    assert hash1.digest() == hash2.digest()

    a[3] = 10
    hash3 = object_state.create_hash(a)

    # Assert that the hash changes when the object changes
    assert hash1.digest() != hash3.digest()

    a[3] = 3
    hash4 = object_state.create_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()


def test_idgraph_pandas_Series():
    """
    Test if idgraph is accurately generated for pandas series
    """
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


def test_hash_pandas_Series():
    """
    Test if hash is accurately generated for pandas series
    """
    s1 = pd.Series([1, 2, 3, 4])

    hash1 = object_state.create_hash(s1)
    hash2 = object_state.create_hash(s1)

    # Assert that the hash does not change when the object remains unchanged
    assert hash1.digest() == hash2.digest()

    s1[2] = 0

    hash3 = object_state.create_hash(s1)

    # Assert that the hash changes when the object changes
    assert hash1.digest() != hash3.digest()

    s1[2] = 3

    hash4 = object_state.create_hash(s1)

    # Assert that the original hash is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()


def test_idgraph_pandas_df():
    """
    Test if idgraph is accurately generated for panda dataframes
    """
    df = sns.load_dataset("penguins")

    idgraph1 = object_state.create_idgraph(df)
    idgraph2 = object_state.create_idgraph(df)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(df)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    df.at[0, "species"] = "Changed"
    idgraph3 = object_state.create_idgraph(df)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    df.at[0, "species"] = "Adelie"
    idgraph4 = object_state.create_idgraph(df)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4

    new_row = {
        "species": "New Species",
        "island": "New island",
        "bill_length_mm": 999,
        "bill_depth_mm": 999,
        "flipper_length_mm": 999,
        "body_mass_g": 999,
        "sex": "Male",
    }
    df.loc[len(df)] = new_row

    idgraph5 = object_state.create_idgraph(df)

    # Assert that idgraph changes when new row is added to dataframe
    assert idgraph1 != idgraph5


def test_hash_pandas_df():
    """
    Test if hash is accurately generated for pandas dataframes
    """
    df = sns.load_dataset("penguins")

    hash1 = object_state.create_hash(df)
    hash2 = object_state.create_hash(df)

    # Assert that the hash does not change when the object remains unchanged
    assert hash1.digest() == hash2.digest()

    df.at[0, "species"] = "Changed"
    hash3 = object_state.create_hash(df)

    # Assert that the hash changes when the object changes
    assert hash1.digest() != hash3.digest()

    df.at[0, "species"] = "Adelie"
    hash4 = object_state.create_hash(df)

    # Assert that the original hash is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()

    new_row = {
        "species": "New Species",
        "island": "New island",
        "bill_length_mm": 999,
        "bill_depth_mm": 999,
        "flipper_length_mm": 999,
        "body_mass_g": 999,
        "sex": "Male",
    }
    df.loc[len(df)] = new_row

    hash5 = object_state.create_hash(df)

    # Assert that hash changes when new row is added to dataframe
    assert hash1.digest() != hash5.digest()


def test_idgraph_matplotlib(matplotlib_plot):
    """
    Test if idgraph is accurately generated for matplotlib objects
    """
    plt = matplotlib_plot[0]
    a = matplotlib_plot[1]

    idgraph1 = object_state.create_idgraph(a)
    idgraph2 = object_state.create_idgraph(a)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(a) and idgraph1.children[0].id_obj == id(a[0])

    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are the same
    assert (pick1 == pick2) == (idgraph1 == idgraph2)

    plt.xlabel("XLABEL_2")
    idgraph3 = object_state.create_idgraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plt.xlabel("XLABEL_1")
    idgraph4 = object_state.create_idgraph(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    assert (pick1 == pick2) == (idgraph1 == idgraph4)

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color("red")
    idgraph5 = object_state.create_idgraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    line.set_color(line_co)
    idgraph6 = object_state.create_idgraph(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    assert (pick1 == pick2) == (idgraph1 == idgraph6)


def test_hash_matplotlib(matplotlib_plot):
    """
    Test if hash is accurately generated for matplotlib objects
    """
    plt = matplotlib_plot[0]
    a = matplotlib_plot[1]

    hash1 = object_state.create_hash(a)
    hash2 = object_state.create_hash(a)

    # Assert that the hash does not change when the object remains unchanged if pickle binaries are the same
    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    assert (pick1 == pick2) == (hash1.digest() == hash2.digest())

    plt.xlabel("XLABEL_2")
    hash3 = object_state.create_hash(a)

    # Assert that the hash changes when the object changes
    assert hash1.digest() != hash3.digest()

    plt.xlabel("XLABEL_1")
    hash4 = object_state.create_hash(a)

    # Assert that the original hash is restored when the original object state is restored if pickle binaries were the same
    assert (pick1 == pick2) == (hash1.digest() == hash4.digest())

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color("red")
    hash5 = object_state.create_hash(a)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash5.digest()

    line.set_color(line_co)
    hash6 = object_state.create_hash(a)

    # Assert that the original hash is restored when the original object state is restored if pickle binaries were the same
    assert (pick1 == pick2) == (hash1.digest() == hash6.digest())


def test_idgraph_seaborn_displot(seaborn_distplot):
    """
    Test if idgraph is accurately generated for seaborn displot objects (figure-level object)
    """
    plot1 = seaborn_distplot

    idgraph1 = object_state.create_idgraph(plot1)
    idgraph2 = object_state.create_idgraph(plot1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    assert (pick1 == pick2) == (idgraph1 == idgraph2)

    plot1.set(xlabel="NEW LABEL")
    idgraph3 = object_state.create_idgraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set(xlabel="flipper_length_mm")
    idgraph4 = object_state.create_idgraph(plot1)
    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    assert (pick1 == pick2) == (idgraph1 == idgraph4)


def test_hash_seaborn_displot(seaborn_distplot):
    """
    Test if hash is accurately generated for seaborn displot objects (figure-level object)
    """
    plot1 = seaborn_distplot

    hash1 = object_state.create_hash(plot1)
    hash2 = object_state.create_hash(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the hash does not change when the object remains unchanged if pickle binaries are same
    assert (pick1 == pick2) == (hash1.digest() == hash2.digest())

    plot1.set(xlabel="NEW LABEL")
    hash3 = object_state.create_hash(plot1)

    # Assert that the hash changes when the object changes
    assert hash1.digest() != hash3.digest()

    plot1.set(xlabel="flipper_length_mm")
    hash4 = object_state.create_hash(plot1)

    # Assert that the original hash is restored when the original object state is restored if pickle binaries were same
    assert (pick1 == pick2) == (hash1.digest() == hash4.digest())


def test_idgraph_seaborn_scatterplot(seaborn_scatterplot):
    """
    Test if idgraph is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    plot1 = seaborn_scatterplot

    idgraph1 = object_state.create_idgraph(plot1)
    idgraph2 = object_state.create_idgraph(plot1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    assert (pick1 == pick2) == (idgraph1 == idgraph2)

    plot1.set_xlabel("Flipper Length")
    idgraph3 = object_state.create_idgraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set_xlabel("flipper_length_mm")
    idgraph4 = object_state.create_idgraph(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    assert (pick1 == pick2) == (idgraph1 == idgraph4)

    plot1.set_facecolor("#eafff5")
    idgraph5 = object_state.create_idgraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5


def test_hash_seaborn_scatterplot(seaborn_scatterplot):
    """
    Test if hash is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    plot1 = seaborn_scatterplot

    hash1 = object_state.create_hash(plot1)
    hash2 = object_state.create_hash(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the hash does not change when the object remains unchanged if pickle binaries are same
    assert (pick1 == pick2) == (hash1.digest() == hash2.digest())

    plot1.set_xlabel("Flipper Length")
    hash3 = object_state.create_hash(plot1)

    # Assert that the hash changes when the object changes
    assert hash1.digest() != hash3.digest()

    plot1.set_xlabel("flipper_length_mm")
    hash4 = object_state.create_hash(plot1)

    # Assert that the original hash is restored when the original object state is restored if pickle binaries were same
    assert (pick1 == pick2) == (hash1.digest() == hash4.digest())

    plot1.set_facecolor("#eafff5")
    hash5 = object_state.create_hash(plot1)

    # Assert that the hash changes when the object changes
    assert hash1.digest() != hash5.digest()
