import pickle
from typing import Generator

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
import seaborn as sns

from kishu.planning.idgraph import IdGraph
from kishu.storage.config import Config


@pytest.fixture()
def enable_experimental_tracker(tmp_kishu_path) -> Generator[type, None, None]:
    prev_value = Config.get("IDGRAPH", "experimental_tracker", True)
    Config.set("IDGRAPH", "experimental_tracker", True)
    yield Config
    Config.set("IDGRAPH", "experimental_tracker", prev_value)


def test_idgraph_simple_list_compare_by_value():
    """
    Test if the idgraph comparisons work. Comparing by value only will identify 'a' as equal
    before and after reassigning, while comparing by structure will report a difference.
    """
    a = [1, 2]
    idgraph1 = IdGraph.from_object(a)
    idgraph2 = IdGraph.from_object(a)

    # reference swap
    a = [1, 2]
    idgraph3 = IdGraph.from_object(a)

    assert idgraph1 == idgraph2
    assert idgraph1 == idgraph3
    assert idgraph1.is_root_id_and_type_equals(idgraph2)
    assert not idgraph1.is_root_id_and_type_equals(idgraph3)


def test_idgraph_nested_list_changed_structure():
    a = [1, 2, 3]
    b = [a, a]
    idgraph1 = IdGraph.from_object(a)

    b[1] = [1, 2, 3]  # Different structure
    idgraph2 = IdGraph.from_object(b)

    assert idgraph1 != idgraph2


def test_idgraph_nested_list_changed_value():
    a = [1, 2, 3]
    b = [a, a]
    idgraph1 = IdGraph.from_object(a)

    b[1][0] = 4
    idgraph2 = IdGraph.from_object(b)

    assert idgraph1 != idgraph2


def test_idgraph_dict_compare_by_value():
    """
    Test if the idgraph comparisons work. Comparing by value only will identify 'a' as equal
    before and after reassigning, while comparing by structure will report a difference.
    """
    a = {"foo": {"bar": "baz"}}
    idgraph1 = IdGraph.from_object(a)

    # reference swap
    a["foo"] = {"bar": "baz"}
    idgraph2 = IdGraph.from_object(a)

    assert idgraph1 == idgraph2


def test_idgraph_numpy():
    """
    Test if idgraph is accurately generated for numpy arrays
    """
    a = np.arange(6)

    idgraph1 = IdGraph.from_object(a)
    idgraph2 = IdGraph.from_object(a)

    # Assert that the obj id is as expected
    assert idgraph1.root_id == id(a)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    a[3] = 10
    idgraph3 = IdGraph.from_object(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    a[3] = 3
    idgraph4 = IdGraph.from_object(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4


def test_idgraph_numpy_nonoverlap():
    """
    Test if idgraph overlaps are accurately detected for numpy arrays.
    """
    a = np.array([6])
    b = np.array([7, 8])

    idgraph1 = IdGraph.from_object(a)
    idgraph2 = IdGraph.from_object(b)

    assert idgraph1.is_overlap(idgraph2)


def test_idgraph_numpy_nonoverlap_experimental(enable_experimental_tracker):
    """
    Test if idgraph overlaps are accurately detected for numpy arrays.
    """
    a = np.array([6])
    b = np.array([7, 8])

    idgraph1 = IdGraph.from_object(a)
    idgraph2 = IdGraph.from_object(b)

    assert not idgraph1.is_overlap(idgraph2)


@pytest.mark.skip(reason="Flaky")
def test_idgraph_pandas_Series():
    """
    Test if idgraph is accurately generated for panda series.
    This test compares by value only as some objects in series are dynamically generated,
    i.e., there will be false positives if comparing via memory address.
    """
    s1 = pd.Series([1, 2, 3, 4])

    idgraph1 = IdGraph.from_object(s1)
    idgraph2 = IdGraph.from_object(s1)

    # Assert that the obj id is as expected
    assert idgraph1.root_id == id(s1)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1.value_equals(idgraph2)

    s1[2] = 0

    idgraph3 = IdGraph.from_object(s1)

    # Assert that the id graph changes when the object changes
    assert not idgraph1.value_equals(idgraph3)

    s1[2] = 3

    idgraph4 = IdGraph.from_object(s1)

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1.value_equals(idgraph4)


def test_idgraph_pandas_df():
    """
    Test if idgraph is accurately generated for panda dataframes with the dirty bit hack enabled
    """
    df = sns.load_dataset("penguins")

    for _, col in df.items():
        col.__array__().flags.writeable = False

    idgraph1 = IdGraph.from_object(df)
    idgraph2 = IdGraph.from_object(df)

    # Assert that the obj id is as expected
    assert idgraph1.root_id == id(df)

    # Assert that the id graph does not change when the object remains unchanged
    assert idgraph1 == idgraph2

    df.at[0, "species"] = "Changed"
    idgraph3 = IdGraph.from_object(df)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    df.at[0, "species"] = "Adelie"
    idgraph4 = IdGraph.from_object(df)

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

    idgraph5 = IdGraph.from_object(df)

    # Assert that idgraph changes when new row is added to dataframe
    assert idgraph1 != idgraph5


def test_idgraph_matplotlib():
    """
    Test if idgraph is accurately generated for matplotlib objects
    """
    plt.close("all")
    df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=["a", "b", "c"])
    a = plt.plot(df["a"], df["b"])
    plt.xlabel("XLABEL_1")

    idgraph1 = IdGraph.from_object(a)
    idgraph2 = IdGraph.from_object(a)

    # Assert that the obj id is as expected
    assert idgraph1.root_id == id(a)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are the same
    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plt.xlabel("XLABEL_2")
    idgraph3 = IdGraph.from_object(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plt.xlabel("XLABEL_1")
    idgraph4 = IdGraph.from_object(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color("red")
    idgraph5 = IdGraph.from_object(a)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    line.set_color(line_co)
    idgraph6 = IdGraph.from_object(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph6
    else:
        assert idgraph1 == idgraph6

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

    idgraph1 = IdGraph.from_object(plot1)
    idgraph2 = IdGraph.from_object(plot1)

    # Assert that the obj id is as expected
    assert idgraph1.root_id == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same

    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plot1.set(xlabel="NEW LABEL")
    idgraph3 = IdGraph.from_object(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set(xlabel="flipper_length_mm")
    idgraph4 = IdGraph.from_object(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

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

    idgraph1 = IdGraph.from_object(plot1)
    print("make idgraph 1")
    idgraph2 = IdGraph.from_object(plot1)
    print("make idgraph 2")

    # Assert that the obj id is as expected
    assert idgraph1.root_id == id(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert idgraph1 != idgraph2
    else:
        assert idgraph1 == idgraph2

    plot1.set_xlabel("Flipper Length")
    idgraph3 = IdGraph.from_object(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set_xlabel("flipper_length_mm")
    idgraph4 = IdGraph.from_object(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    plot1.set_facecolor("#eafff5")
    idgraph5 = IdGraph.from_object(plot1)

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    # Close all figures
    plt.close("all")


def test_idgraph_primitive_nonoverlap():
    """
    Primitives stored in fixed memory addresses are assumed to not overlap.
    """
    a, b, c, d = 1, 2, 3, 4
    list1 = [a, b, c]
    list2 = [b, c, d]

    idgraph1 = IdGraph.from_object(list1)
    idgraph2 = IdGraph.from_object(list2)

    assert not idgraph1.is_overlap(idgraph2)


def test_idgraph_nonprimitive_nonoverlap():
    a, b, c, d = [], [], [], []
    list1 = [a, b]
    list2 = [c, d]

    idgraph1 = IdGraph.from_object(list1)
    idgraph2 = IdGraph.from_object(list2)

    assert not idgraph1.is_overlap(idgraph2)


def test_idgraph_nested_overlap():
    a, b, c, d = 1, 2, 3, 4
    list = [a, b, c]
    nested_list = [list, d]

    idgraph1 = IdGraph.from_object(list)
    idgraph2 = IdGraph.from_object(nested_list)

    assert idgraph1.is_overlap(idgraph2)


def test_idgraph_generator():
    """
    Generators are assumed to be modified on access (i.e., whenever a new ID graph is computed for it).
    """
    gen = (i for i in range(10))
    idgraph1 = IdGraph.from_object(gen)
    idgraph2 = IdGraph.from_object(gen)
    assert idgraph1 != idgraph2
    assert idgraph1.is_overlap(idgraph2)


def test_idgraph_functiontype():
    """
    Functiontypes overlap with their accessed globals.
    """
    globals_dict = {}
    function_str = """
def test():
    global x
    x = []
"""
    exec("x = set()", globals_dict)
    exec(function_str, globals_dict)
    idgraph1 = IdGraph.from_object(globals_dict["x"])
    idgraph2 = IdGraph.from_object(globals_dict["test"])
    assert idgraph1.is_overlap(idgraph2)
