import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
import seaborn as sns
import pytest

from kishu.planning.C_implementation.object_state_c import ObjectState

def benchmark_hash_creation(obj):
    objs1 = ObjectState(obj)

def benchmark_hash_comparison(objs1: ObjectState, objs2: ObjectState):
    return objs1.compare_ObjectStates(objs2)

#--------------------------------------- Numpy tests -----------------------
def test_hash_numpy():
    """
        Test if hash is accurately generated for numpy arrays
    """
    a = np.arange(6)

    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    # Assert that the hash does not change when the object remains unchanged
    assert objs1.compare_ObjectStates(objs2) == True

    a[3] = 10
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

    a[3] = 3
    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    assert objs1.compare_ObjectStates(objs2) == True

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

    hash_equal = benchmark(benchmark_hash_comparison, objs1, objs2)
    assert True
    
#--------------------------------------- Pandas tests ----------------------
def test_hash_pandas_Series():
    """
        Test if hash is accurately generated for pandas series
    """
    a = pd.Series([1, 2, 3, 4])

    objs1 = ObjectState(a)
    objs2 = ObjectState(a)

    # Assert that the hash does not change when the object remains unchanged
    assert objs1.compare_ObjectStates(objs2) == True

    a[2] = 0
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

    a[2] = 3

    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    assert objs1.compare_ObjectStates(objs2) == True

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

    hash_equal = benchmark(benchmark_hash_comparison, objs1, objs2)
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
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

    df.at[0, 'species'] = "Changed"
    objs2.update_object_hash(df)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

    df.at[0, 'species'] = "Adelie"
    objs2.update_object_hash(df)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(df)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

    new_row = {'species': "New Species", 'island': "New island", 'bill_length_mm': 999,
               'bill_depth_mm': 999, 'flipper_length_mm': 999, 'body_mass_g': 999, 'sex': "Male"}
    df.loc[len(df)] = new_row

    objs2.update_object_hash(df)

    # Assert that hash changes when new row is added to dataframe
    assert objs1.compare_ObjectStates(objs2) == False

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

    hash_equal = benchmark(benchmark_hash_comparison, objs1, objs2)
    assert True

#--------------------------------------- matplotlib tests ----------------------
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
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

    plt.xlabel("XLABEL_2")
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

    plt.xlabel("XLABEL_1")
    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored 
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(a)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color('red')
    objs2.update_object_hash(a)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

    line.set_color(line_co)
    objs2.update_object_hash(a)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(a)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

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

    hash_equal = benchmark(benchmark_hash_comparison, objs1, objs2)
    plt.close('all')
    assert True

#--------------------------------------- seaborn tests ----------------------
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
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

    plot1.set(xlabel="NEW LABEL")
    objs2.update_object_hash(plot1)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

    plot1.set(xlabel="flipper_length_mm")
    objs2.update_object_hash(plot1)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(plot1)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

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

    hash_equal = benchmark(benchmark_hash_comparison, objs1, objs2)
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
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

    plot1.set_xlabel('Flipper Length')
    objs2.update_object_hash(plot1)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

    plot1.set_xlabel('flipper_length_mm')
    objs2.update_object_hash(plot1)

    # Assert that the original hash is restored when the original object state is restored
    # (if pickled binaries are the same)
    pickled2 = pickle.dumps(plot1)
    if pickled1 == pickled2:
        assert objs1.compare_ObjectStates(objs2) == True
    else:
        assert objs1.compare_ObjectStates(objs2) == False

    plot1.set_facecolor('#eafff5')
    objs2.update_object_hash(plot1)

    # Assert that the hash changes when the object changes
    assert objs1.compare_ObjectStates(objs2) == False

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

    hash_equal = benchmark(benchmark_hash_comparison, objs1, objs2)
    plt.close('all')
    assert True
