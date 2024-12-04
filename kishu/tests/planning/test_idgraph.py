import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
import seaborn as sns

from kishu.planning.idgraph import GraphNode, IdGraph, ObjectId


def test_idgraph_simple_list_compare_by_value():
    """
    Test if the idgraph comparisons work. Comparing by value only will identify 'a' as equal
    before and after reassigning, while comparing by structure will report a difference.
    """
    a = [1, 2]
    idgraph1 = IdGraph(a)

    # reference swap
    a = [1, 2]
    idgraph2 = IdGraph(a)

    assert idgraph1 != idgraph2
    assert idgraph1.value_equals(idgraph2)


def test_idgraph_nested_list_compare_by_value():
    a = [1, 2, 3]
    b = [a, a]
    idgraph1 = IdGraph(a)

    b[1] = [1, 2, 3]  # Different list from a
    idgraph2 = IdGraph(b)

    assert idgraph1 != idgraph2
    assert not idgraph1.value_equals(idgraph2)


def test_idgraph_dict_compare_by_value():
    """
    Test if the idgraph comparisons work. Comparing by value only will identify 'a' as equal
    before and after reassigning, while comparing by structure will report a difference.
    """
    a = {"foo": {"bar": "baz"}}
    idgraph1 = IdGraph(a)

    # reference swap
    a["foo"] = {"bar": "baz"}
    idgraph2 = IdGraph(a)

    assert idgraph1 != idgraph2
    assert idgraph1.value_equals(idgraph2)


def test_idgraph_numpy():
    """
    Test if idgraph is accurately generated for numpy arrays
    """
    a = np.arange(6)

    idgraph1 = IdGraph(a)
    idgraph2 = IdGraph(a)

    # Assert that the obj id is as expected
    assert idgraph1._root.obj_id == ObjectId(id(a))

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    a[3] = 10
    idgraph3 = IdGraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    a[3] = 3
    idgraph4 = IdGraph(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4


def test_hash_numpy():
    """
    Test if idgraph is accurately generated for numpy arrays
    """
    a = np.arange(6)

    hash1 = GraphNode.get_object_hash(a)
    hash2 = GraphNode.get_object_hash(a)

    # Assert that the hash does not change when the object remains unchanged
    assert hash1.digest() == hash2.digest()

    a[3] = 10
    hash3 = GraphNode.get_object_hash(a)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    a[3] = 3
    hash4 = GraphNode.get_object_hash(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()


@pytest.mark.skip(reason="Flaky")
def test_idgraph_pandas_Series():
    """
    Test if idgraph is accurately generated for panda series.
    This test compares by value only as some objects in series are dynamically generated,
    i.e., there will be false positives if comparing via memory address.
    """
    s1 = pd.Series([1, 2, 3, 4])

    idgraph1 = IdGraph(s1)
    idgraph2 = IdGraph(s1)

    # Assert that the obj id is as expected
    assert idgraph1._root.obj_id == id(s1)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1.value_equals(idgraph2)

    s1[2] = 0

    idgraph3 = IdGraph(s1)

    # Assert that the id graph changes when the object changes
    assert not idgraph1.value_equals(idgraph3)

    s1[2] = 3

    idgraph4 = IdGraph(s1)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1.value_equals(idgraph4)


def test_hash_pandas_Series():
    """
    Test if idgraph is accurately generated for panda series
    """
    s1 = pd.Series([1, 2, 3, 4])

    hash1 = GraphNode.get_object_hash(s1)
    hash2 = GraphNode.get_object_hash(s1)

    # Assert that the hash does not change when the object remains unchanged
    assert hash1.digest() == hash2.digest()

    s1[2] = 0

    hash3 = GraphNode.get_object_hash(s1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    s1[2] = 3

    hash4 = GraphNode.get_object_hash(s1)

    # Assert that the original id graph is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()


def test_idgraph_pandas_df():
    """
    Test if idgraph is accurately generated for panda dataframes with the dirty bit hack enabled
    """
    df = sns.load_dataset("penguins")

    for _, col in df.items():
        col.__array__().flags.writeable = False

    idgraph1 = IdGraph(df)
    idgraph2 = IdGraph(df)

    # Assert that the obj id is as expected
    assert idgraph1._root.obj_id == ObjectId(id(df))

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    df.at[0, "species"] = "Changed"
    idgraph3 = IdGraph(df)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    df.at[0, "species"] = "Adelie"
    idgraph4 = IdGraph(df)

    # Assert that with the hack, the equality is solely based on whether the current dataframe
    # (hash4) is dirty or not, even though idgraph1 and idgraph4 are id graphs
    # for equal dataframes.
    assert idgraph1 != idgraph4

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

    idgraph5 = IdGraph(df)

    # Assert that idgraph changes when new row is added to dataframe
    assert idgraph1 != idgraph5


def test_hash_pandas_df():
    """
    Test if idgraph is accurately generated for panda dataframes
    """
    df = sns.load_dataset("penguins")

    hash1 = GraphNode.get_object_hash(df)
    hash2 = GraphNode.get_object_hash(df)

    # Assert that the id graph does not change when the object remains unchanged
    assert hash1.digest() == hash2.digest()

    df.at[0, "species"] = "Changed"
    hash3 = GraphNode.get_object_hash(df)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    df.at[0, "species"] = "Adelie"
    hash4 = GraphNode.get_object_hash(df)

    # Assert that the original id graph is restored when the original object state is restored
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

    hash5 = GraphNode.get_object_hash(df)

    # Assert that idgraph changes when new row is added to dataframe
    assert hash1.digest() != hash5.digest()


def test_idgraph_matplotlib():
    """
    Test if idgraph is accurately generated for matplotlib objects
    """
    plt.close("all")
    df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=["a", "b", "c"])
    a = plt.plot(df["a"], df["b"])
    plt.xlabel("XLABEL_1")

    idgraph1 = IdGraph(a)
    idgraph2 = IdGraph(a)

    # Assert that the obj id is as expected
    assert idgraph1._root.obj_id.obj_id == id(a) and idgraph1._root.children[0].obj_id.obj_id == id(a[0])

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are the same
    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plt.xlabel("XLABEL_2")
    idgraph3 = IdGraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plt.xlabel("XLABEL_1")
    idgraph4 = IdGraph(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color("red")
    idgraph5 = IdGraph(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    line.set_color(line_co)
    idgraph6 = IdGraph(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph6
    else:
        assert idgraph1 == idgraph6

    # Close all figures
    plt.close("all")


def test_hash_matplotlib():
    """
    Test if idgraph is accurately generated for matplotlib objects
    """
    plt.close("all")
    df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=["a", "b", "c"])
    a = plt.plot(df["a"], df["b"])
    plt.xlabel("XLABEL_1")

    hash1 = GraphNode.get_object_hash(a)
    hash2 = GraphNode.get_object_hash(a)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are the same
    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    if pick1 != pick2:
        assert hash1.digest() != hash2.digest()
    else:
        assert hash1.digest() == hash2.digest()

    plt.xlabel("XLABEL_2")
    hash3 = GraphNode.get_object_hash(a)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    plt.xlabel("XLABEL_1")
    hash4 = GraphNode.get_object_hash(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert hash1.digest() != hash4.digest()
    else:
        assert hash1.digest() == hash4.digest()

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color("red")
    hash5 = GraphNode.get_object_hash(a)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash5.digest()

    line.set_color(line_co)
    hash6 = GraphNode.get_object_hash(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert hash1.digest() != hash6.digest()
    else:
        assert hash1.digest() == hash6.digest()

    # Close all figures
    plt.close("all")


def test_idgraph_seaborn_displot():
    """
    Test if idgraph is accurately generated for seaborn displot objects (figure-level object)
    """
    plt.close("all")
    df = sns.load_dataset("penguins")
    plot1 = sns.displot(data=df, x="flipper_length_mm", y="bill_length_mm", kind="hist")
    plot1.set(xlabel="flipper_length_mm")

    idgraph1 = IdGraph(plot1)
    idgraph2 = IdGraph(plot1)

    # Assert that the obj id is as expected
    assert idgraph1._root.obj_id.obj_id == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same

    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plot1.set(xlabel="NEW LABEL")
    idgraph3 = IdGraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set(xlabel="flipper_length_mm")
    idgraph4 = IdGraph(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    # Close all figures
    plt.close("all")


def test_hash_seaborn_displot():
    """
    Test if idgraph is accurately generated for seaborn displot objects (figure-level object)
    """
    plt.close("all")
    df = sns.load_dataset("penguins")
    plot1 = sns.displot(data=df, x="flipper_length_mm", y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    hash1 = GraphNode.get_object_hash(plot1)
    hash2 = GraphNode.get_object_hash(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert hash1.digest() != hash2.digest()
    else:
        assert hash1.digest() == hash2.digest()

    plot1.set(xlabel="NEW LABEL")
    hash3 = GraphNode.get_object_hash(plot1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    plot1.set(xlabel="flipper_length_mm")
    hash4 = GraphNode.get_object_hash(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert hash1.digest() != hash4.digest()
    else:
        assert hash1.digest() == hash4.digest()

    # Close all figures
    plt.close("all")


def test_idgraph_seaborn_scatterplot():
    """
    Test if idgraph is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    # Close all figures
    plt.close("all")

    df = sns.load_dataset("penguins")
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel("flipper_length_mm")
    plot1.set_facecolor("white")

    idgraph1 = IdGraph(plot1)
    print("make idgraph 1")
    idgraph2 = IdGraph(plot1)
    print("make idgraph 2")

    # Assert that the obj id is as expected
    assert idgraph1._root.obj_id.obj_id == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plot1.set_xlabel("Flipper Length")
    idgraph3 = IdGraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set_xlabel("flipper_length_mm")
    idgraph4 = IdGraph(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    plot1.set_facecolor("#eafff5")
    idgraph5 = IdGraph(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    # Close all figures
    plt.close("all")


def test_hash_seaborn_scatterplot():
    """
    Test if idgraph is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    plt.close("all")
    df = sns.load_dataset("penguins")
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel("flipper_length_mm")
    plot1.set_facecolor("white")

    hash1 = GraphNode.get_object_hash(plot1)
    hash2 = GraphNode.get_object_hash(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert hash1.digest() != hash2.digest()
    else:
        assert hash1.digest() == hash2.digest()

    plot1.set_xlabel("Flipper Length")
    hash3 = GraphNode.get_object_hash(plot1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    plot1.set_xlabel("flipper_length_mm")
    hash4 = GraphNode.get_object_hash(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert hash1.digest() != hash4.digest()
    else:
        assert hash1.digest() == hash4.digest()

    plot1.set_facecolor("#eafff5")
    hash5 = GraphNode.get_object_hash(plot1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash5.digest()

    # Close all figures
    plt.close("all")


def test_idgraph_primitive_nonoverlap():
    """
    Primitives are assumed to never overlap.
    """
    a, b, c, d = 1, 2, "3", 4
    list1 = [a, b, c]
    list2 = [b, c, d]

    idgraph1 = IdGraph(list1)
    idgraph2 = IdGraph(list2)

    assert not idgraph1.is_overlap(idgraph2)


def test_idgraph_no_overlap():
    a, b, c, d = [], [], [], []
    list1 = [a, b]
    list2 = [c, d]

    idgraph1 = IdGraph(list1)
    idgraph2 = IdGraph(list2)

    assert not idgraph1.is_overlap(idgraph2)


def test_idgraph_nested_overlap():
    a, b, c, d = 1, 2, 3, 4
    list = [a, b, c]
    nested_list = [list, d]

    idgraph1 = IdGraph(list)
    idgraph2 = IdGraph(nested_list)

    assert idgraph1.is_overlap(idgraph2)


def test_idgraph_generator():
    """
    Generators are assumed to be modified on access (i.e., whenever a new ID graph is computed for it).
    """
    gen = (i for i in range(10))
    idgraph1 = IdGraph(gen)
    idgraph2 = IdGraph(gen)
    print(idgraph1._id_list)
    print(idgraph2._id_list)
    assert idgraph1 != idgraph2
    assert idgraph1.is_overlap(idgraph2)
