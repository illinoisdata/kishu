import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
import seaborn as sns
import pytest

from lib.object_state_c import ObjectState


def benchmark_hash_creation(obj):
    ObjectState(obj)


def benchmark_hash_comparison(objs1: ObjectState, objs2: ObjectState):
    return objs1.compare_ObjectStates(objs2)

# --------------------------------------- Simple tests -----------------------


def test_idgraph_simple_list_compare_by_value():
    """
        Test if the idgraph comparisons work. Comparing by value only will identify 'a' as equal
        before and after reassigning, while comparing by structure will report a difference.
    """
    a = [1, 2]
    objs1 = ObjectState(a)

    # reference swap
    a = [1, 2]
    objs2 = ObjectState(a)

    assert not objs1.compare_ObjectStates(objs2)


def test_idgraph_nested_list_compare_by_value():
    a = [1, 2, 3]
    b = [a, a]
    objs1 = ObjectState(a)

    b[1] = [1, 2, 3]  # Different list from a
    objs2 = ObjectState(b)

    assert not objs1.compare_ObjectStates(objs2)


def test_idgraph_dict_compare_by_value():
    """
        Test if the idgraph comparisons work. Comparing by value only will identify 'a' as equal
        before and after reassigning, while comparing by structure will report a difference.
    """
    a = {"foo": {"bar": "baz"}}
    objs1 = ObjectState(a)

    # reference swap
    a["foo"] = {"bar": "baz"}
    objs2 = ObjectState(a)

    assert not objs1.compare_ObjectStates(objs2)


def test_traversal():
    a = [1, [2, 3]]
    objs1 = ObjectState(a)

    a[1][1] = [3]  # a = [1, [2, [3]]]
    objs2 = ObjectState(a)

    assert not objs1.compare_ObjectStates(objs2)


def test_list_vs_tuple():
    a = [1, 2]
    b = (1, 2)

    objs1 = ObjectState(a)
    objs2 = ObjectState(b)

    assert not objs1.compare_ObjectStates(objs2)


def test_idgraph_overlap():
    a, b, c = 1, 2, 3
    list1 = [a, b]
    list2 = [b, c]

    objs1 = ObjectState(list1, True)
    objs2 = ObjectState(list2, True)

    assert objs1.is_overlap(objs2)


def test_idgraph_no_overlap():
    a, b, c, d = 1, 2, 3, 4
    list1 = [a, b]
    list2 = [c, d]

    objs1 = ObjectState(list1, True)
    objs2 = ObjectState(list2, True)

    assert not objs1.is_overlap(objs2)


def test_idgraph_nested_overlap():
    a, b, c, d = 1, 2, 3, 4
    list = [a, b, c]
    nested_list = [list, d]

    objs1 = ObjectState(list, True)
    objs2 = ObjectState(nested_list, True)

    assert objs1.is_overlap(objs2)
# --------------------------------------- Numpy tests -----------------------


def test_hash_numpy():
    """
        Test if hash is accurately generated for numpy arrays
    """
    a = np.arange(6)

    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    # Assert that the hash does not change when the object remains unchanged
    assert objs1.compare_ObjectStates(objs2)

    a[3] = 10
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    a[3] = 3
    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    assert objs1.compare_ObjectStates(objs2)


@pytest.mark.benchmark(group="hash creation")
def test_hash_creation_numpy(benchmark):
    a = np.arange(6)

    benchmark(benchmark_hash_creation, a)
    assert True


@pytest.mark.benchmark(group="hash comparison")
def test_hash_comparison_numpy(benchmark):
    a = np.arange(6)

    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    benchmark(benchmark_hash_comparison, objs1, objs2)
    assert True

# --------------------------------------- Pandas tests ----------------------


def test_hash_pandas_Series():
    """
        Test if hash is accurately generated for pandas series
    """
    a = pd.Series([1, 2, 3, 4])

    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    # Assert that the hash does not change when the object remains unchanged
    assert objs1.compare_ObjectStates(objs2)

    a[2] = 0
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    a[2] = 3

    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    assert objs1.compare_ObjectStates(objs2)


@pytest.mark.benchmark(group="hash creation")
def test_hash_creation_series(benchmark):
    a = pd.Series([1, 2, 3, 4])
    benchmark(benchmark_hash_creation, a)
    assert True


@pytest.mark.benchmark(group="hash comparison")
def test_hash_comparison_series(benchmark):
    a = pd.Series([1, 2, 3, 4])
    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    benchmark(benchmark_hash_comparison, objs1, objs2)
    assert True


def test_hash_pandas_df():
    """
        Test if hash is accurately generated for pandas dataframes
    """
    df = sns.load_dataset('penguins')

    objs1 = ObjectState(df)
    objs2 = ObjectState(df)

    pickled1 = pickle.dumps(df)
    pickled2 = pickle.dumps(df)

    # Assert that the hash does not change when the object remains unchanged
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    df.at[0, 'species'] = "Changed"
    objs2.update_object_hash(df)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    df.at[0, 'species'] = "Adelie"
    objs2.update_object_hash(df)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(df)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    new_row = {'species': "New Species", 'island': "New island", 'bill_length_mm': 999,
               'bill_depth_mm': 999, 'flipper_length_mm': 999, 'body_mass_g': 999, 'sex': "Male"}
    df.loc[len(df)] = new_row

    objs2.update_object_hash(df)

    # Assert that hash changes when new row is added to dataframe
    assert not objs1.compare_ObjectStates(objs2)


@pytest.mark.benchmark(group="hash creation")
def test_hash_creation_df(benchmark):
    df = sns.load_dataset('penguins')
    benchmark(benchmark_hash_creation, df)
    assert True


@pytest.mark.benchmark(group="hash comparison")
def test_hash_compare_df(benchmark):
    df = sns.load_dataset('penguins')

    objs1 = ObjectState(df)
    objs2 = ObjectState(df)

    benchmark(benchmark_hash_comparison, objs1, objs2)
    assert True

# --------------------------------------- matplotlib tests ----------------------


def test_hash_matplotlib():
    """
        Test if hash is accurately generated for matplotlib objects
    """
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    pickled1 = pickle.dumps(a)
    pickled2 = pickle.dumps(a)

    # Assert that the hash does not change when the object remains unchanged
    # (if pickled binaries are the same)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    plt.xlabel("XLABEL_2")
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    plt.xlabel("XLABEL_1")
    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(a)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color('red')
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    line.set_color(line_co)
    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(a)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    # Close all figures
    plt.close('all')


@pytest.mark.benchmark(group="hash creation")
def test_hash_creation_matplotlib(benchmark):
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    benchmark(benchmark_hash_creation, a)
    plt.close('all')
    assert True


@pytest.mark.benchmark(group="hash comparison")
def test_hash_compare_matplotlib(benchmark):
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])

    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    benchmark(benchmark_hash_comparison, objs1, objs2)
    plt.close('all')
    assert True

# --------------------------------------- seaborn tests ----------------------


def test_hash_sns_displot():
    """
        Test if hash is accurately generated for seaborn displot objects (figure-level object)
    """
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    objs1 = ObjectState(plot1)
    objs2 = ObjectState(plot1)

    pickled1 = pickle.dumps(plot1)
    pickled2 = pickle.dumps(plot1)

    # Assert that the hash does not change when the object remains unchanged
    # (if pickled binaries are the same)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    plot1.set(xlabel="NEW LABEL")
    objs2.update_object_hash(plot1)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    plot1.set(xlabel="flipper_length_mm")
    objs2.update_object_hash(plot1)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(plot1)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    # Close all figures
    plt.close('all')


@pytest.mark.benchmark(group="hash creation")
def test_hash_creation_sns_displot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")
    benchmark(benchmark_hash_creation, plot1)
    plt.close('all')
    assert True


@pytest.mark.benchmark(group="hash comparison")
def test_compare_hash_sns_displot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    objs1 = ObjectState(plot1)
    objs2 = ObjectState(plot1)

    benchmark(benchmark_hash_comparison, objs1, objs2)
    plt.close('all')
    assert True


def test_hash_sns_scatterplot():
    """
        Test if hash is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    objs1 = ObjectState(plot1)
    objs2 = ObjectState(plot1)

    pickled1 = pickle.dumps(plot1)
    pickled2 = pickle.dumps(plot1)

    # Assert that the hash does not change when the object remains unchanged
    # (if pickled binaries are the same)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    plot1.set_xlabel('Flipper Length')
    objs2.update_object_hash(plot1)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    plot1.set_xlabel('flipper_length_mm')
    objs2.update_object_hash(plot1)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(plot1)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2)
    else:
        assert not objs1.compare_ObjectStates(objs2)

    plot1.set_facecolor('#eafff5')
    objs2.update_object_hash(plot1)

    # Assert that the hash changes when the object changes
    assert not objs1.compare_ObjectStates(objs2)

    # Close all figures
    plt.close('all')


@pytest.mark.benchmark(group="hash creation")
def test_hash_creation_sns_scatterplot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')
    benchmark(benchmark_hash_creation, plot1)
    plt.close('all')
    assert True


@pytest.mark.benchmark(group="hash comparison")
def test_hash_compare_sns_scatterplot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    objs1 = ObjectState(plot1)
    objs2 = ObjectState(plot1)

    benchmark(benchmark_hash_comparison, objs1, objs2)
    plt.close('all')
    assert True

# --------------------------------------- df benchmarks ----------------------


def make_df(rows, cols):
    num_rows = rows
    num_cols = cols
    data = {}
    for i in range(num_cols):
        col_name = f'col{i+1}'
        data[col_name] = np.random.randint(low=0, high=100, size=num_rows)
    df = pd.DataFrame(data)
    return df


@pytest.mark.benchmark(group="dataframe benchmarks")
def test_df_1k_rows_10_cols(benchmark):
    df = make_df(1000, 10)
    benchmark(benchmark_hash_creation, df)
    assert True


@pytest.mark.benchmark(group="dataframe benchmarks")
def test_df_10k_rows_10_cols(benchmark):
    df = make_df(10000, 10)
    benchmark(benchmark_hash_creation, df)
    assert True


@pytest.mark.benchmark(group="dataframe benchmarks")
def test_df_100k_rows_10_cols(benchmark):
    df = make_df(100000, 10)
    benchmark(benchmark_hash_creation, df)
    assert True


@pytest.mark.benchmark(group="dataframe benchmarks")
def test_df_1M_rows_10_cols(benchmark):
    df = make_df(1000000, 10)
    benchmark(benchmark_hash_creation, df)
    assert True
