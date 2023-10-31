import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
import seaborn as sns
import xxhash

from kishu.planning.idgraph import get_object_hash, get_object_state


def benchmark_idgraph_creation(obj):
    idgraph1 = get_object_state(obj, {})
    return idgraph1


def benchmark_idgraph_comparison(idgraph1, idgraph2):
    return idgraph1 == idgraph2


def benchmark_hash_creation(obj):
    hash1 = get_object_hash(obj)
    return hash1


def benchmark_hash_comparison(hash1: xxhash, hash2: xxhash):
    return hash1.digest() == hash2.digest()


def test_idgraph_numpy():
    """
        Test if idgraph is accurately generated for numpy arrays
    """
    a = np.arange(6)

    idgraph1 = get_object_state(a, {})
    idgraph2 = get_object_state(a, {})

    # init_comparison, idgraph1 = benchmark(benchmark_idgraph_ret_comp_id, a)

    # Assert that the id graph does not change when the object remains unchanged
    # assert init_comparison
    assert idgraph1 == idgraph2

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(a)

    a[3] = 10
    idgraph3 = get_object_state(a, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    a[3] = 3
    idgraph4 = get_object_state(a, {})

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4


def test_idgraph_creation_numpy(benchmark):
    a = np.arange(6)

    benchmark(benchmark_idgraph_creation, a)
    assert True


def test_idgraph_comparison_numpy(benchmark):
    a = np.arange(6)

    idgraph1 = get_object_state(a, {})
    idgraph2 = get_object_state(a, {})

    idgraph_equal = benchmark(benchmark_idgraph_comparison, idgraph1, idgraph2)
    assert idgraph_equal


def test_hash_numpy():
    """
        Test if idgraph is accurately generated for numpy arrays
    """
    a = np.arange(6)

    hash1 = get_object_hash(a)
    hash2 = get_object_hash(a)
    # init_comparison, hash1 = benchmark(benchmark_hash_ret_comp_hash, a)

    # Assert that the hash does not change when the object remains unchanged
    # assert init_comparison
    assert hash1.digest() == hash2.digest()

    a[3] = 10
    hash3 = get_object_hash(a)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    a[3] = 3
    hash4 = get_object_hash(a)

    # Assert that the original id graph is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()


def test_hash_creation_numpy(benchmark):
    a = np.arange(6)

    benchmark(benchmark_hash_creation, a)
    assert True


def test_hash_comparison_numpy(benchmark):
    a = np.arange(6)

    hash1 = get_object_hash(a)
    hash2 = get_object_hash(a)

    hash_equal = benchmark(benchmark_hash_comparison, hash1, hash2)
    assert hash_equal


def test_idgraph_pandas_Series():
    """
        Test if idgraph is accurately generated for panda series
    """

    # with open('myfile.txt', 'a') as file:
    #     file.write(pd.__version__ + "\n")
    #     file.write('numpy version: ' + np.__version__ + "\n")
    #     file.write('seaborn version: ' + sns.__version__ + "\n")
    # print(f'Pandas version: {pd.__version__}')
    # print(f'Numpy version: {np.__version__}')
    # print(f'Seaborn version: {sns.__version__}')
    # print(f'Pickle version: {pickle.format_version}')
    s1 = pd.Series([1, 2, 3, 4])

    idgraph1 = get_object_state(s1, {})
    idgraph2 = get_object_state(s1, {})
    # init_comparison, idgraph1 = benchmark(benchmark_idgraph_ret_comp_id, s1)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(s1)

    # Assert that the id graph does not change when the object remains unchanged
    # assert init_comparison
    assert idgraph1 == idgraph2

    s1[2] = 0

    idgraph3 = get_object_state(s1, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    s1[2] = 3

    idgraph4 = get_object_state(s1, {})

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4


def test_idgraph_creation_pandas_Series(benchmark):
    s1 = pd.Series([1, 2, 3, 4])

    benchmark(benchmark_idgraph_creation, s1)
    assert True


def test_idgraph_comparison_pandas_Series(benchmark):
    s1 = pd.Series([1, 2, 3, 4])

    idgraph1 = get_object_state(s1, {})
    idgraph2 = get_object_state(s1, {})

    idgraph_equal = benchmark(benchmark_idgraph_comparison, idgraph1, idgraph2)
    assert idgraph_equal


def test_hash_pandas_Series():
    """
        Test if idgraph is accurately generated for panda series
    """
    s1 = pd.Series([1, 2, 3, 4])

    hash1 = get_object_hash(s1)
    hash2 = get_object_hash(s1)
    # init_comparison, hash1 = benchmark(benchmark_hash_ret_comp_hash, s1)

    # Assert that the hash does not change when the object remains unchanged
    # assert init_comparison
    assert hash1.digest() == hash2.digest()

    s1[2] = 0

    hash3 = get_object_hash(s1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    s1[2] = 3

    hash4 = get_object_hash(s1)

    # Assert that the original id graph is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()


def test_hash_creation_pandas_Series(benchmark):
    s1 = pd.Series([1, 2, 3, 4])

    benchmark(benchmark_hash_creation, s1)
    assert True


def test_hash_comparison_pandas_Series(benchmark):
    s1 = pd.Series([1, 2, 3, 4])

    hash1 = get_object_hash(s1)
    hash2 = get_object_hash(s1)

    hash_equal = benchmark(benchmark_hash_comparison, hash1, hash2)
    assert hash_equal


def test_idgraph_pandas_df():
    """
        Test if idgraph is accurately generated for panda dataframes
    """
    df = sns.load_dataset('penguins')

    idgraph1 = get_object_state(df, {})
    idgraph2 = get_object_state(df, {})
    # init_comparison, idgraph1 = benchmark(benchmark_idgraph_ret_comp_id, df)

    # Assert that the obj id is as expected
    assert idgraph1.id_obj == id(df)

    # Assert that the id graph does not change when the object remains unchanged
    # assert init_comparison
    assert idgraph1 == idgraph2

    df.at[0, 'species'] = "Changed"
    idgraph3 = get_object_state(df, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    df.at[0, 'species'] = "Adelie"
    idgraph4 = get_object_state(df, {})

    # Assert that the original id graph is restored when the original object state is restored
    assert idgraph1 == idgraph4

    new_row = {'species': "New Species", 'island': "New island", 'bill_length_mm': 999,
               'bill_depth_mm': 999, 'flipper_length_mm': 999, 'body_mass_g': 999, 'sex': "Male"}
    df.loc[len(df)] = new_row

    idgraph5 = get_object_state(df, {})

    # Assert that idgraph changes when new row is added to dataframe
    assert idgraph1 != idgraph5


def test_idgraph_creation_pandas_df(benchmark):
    df = sns.load_dataset('penguins')

    benchmark(benchmark_idgraph_creation, df)
    assert True


def test_idgraph_comparison_pandas_df(benchmark):
    df = sns.load_dataset('penguins')

    idgraph1 = get_object_state(df, {})
    idgraph2 = get_object_state(df, {})

    idgraph_equal = benchmark(benchmark_idgraph_comparison, idgraph1, idgraph2)
    assert idgraph_equal


def test_hash_pandas_df():
    """
        Test if idgraph is accurately generated for panda dataframes
    """
    df = sns.load_dataset('penguins')

    hash1 = get_object_hash(df)
    hash2 = get_object_hash(df)
    # init_comparison, hash1 = benchmark(benchmark_hash_ret_comp_hash, df)

    # Assert that the id graph does not change when the object remains unchanged
    # assert init_comparison
    assert hash1.digest() == hash2.digest()

    df.at[0, 'species'] = "Changed"
    hash3 = get_object_hash(df)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    df.at[0, 'species'] = "Adelie"
    hash4 = get_object_hash(df)

    # Assert that the original id graph is restored when the original object state is restored
    assert hash1.digest() == hash4.digest()

    new_row = {'species': "New Species", 'island': "New island", 'bill_length_mm': 999,
               'bill_depth_mm': 999, 'flipper_length_mm': 999, 'body_mass_g': 999, 'sex': "Male"}
    df.loc[len(df)] = new_row

    hash5 = get_object_hash(df)

    # Assert that idgraph changes when new row is added to dataframe
    assert hash1.digest() != hash5.digest()


def test_hash_creation_pandas_df(benchmark):
    df = sns.load_dataset('penguins')

    benchmark(benchmark_hash_creation, df)
    assert True


def test_hash_comparison_pandas_df(benchmark):
    df = sns.load_dataset('penguins')

    hash1 = get_object_hash(df)
    hash2 = get_object_hash(df)

    hash_equal = benchmark(benchmark_hash_comparison, hash1, hash2)
    assert hash_equal


def test_idgraph_matplotlib():
    """
        Test if idgraph is accurately generated for matplotlib objects
    """
    # In Python version 3.10.12 and matplotlib version 3.8.0, pickled binaries are not equal

    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    idgraph1 = get_object_state(a, {})
    idgraph2 = get_object_state(a, {})
    # init_comparison, idgraph1 = benchmark(benchmark_idgraph_ret_comp_id, a)

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
    idgraph3 = get_object_state(a, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plt.xlabel("XLABEL_1")
    idgraph4 = get_object_state(a, {})

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color('red')
    idgraph5 = get_object_state(a, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    line.set_color(line_co)
    idgraph6 = get_object_state(a, {})

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert idgraph1 != idgraph6
    else:
        assert idgraph1 == idgraph6

    # Close all figures
    plt.close('all')


def test_idgraph_ceation_matplotlib(benchmark):
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    benchmark(benchmark_idgraph_creation, a)
    assert True
    plt.close('all')


def test_idgraph_comparison_matplotlib(benchmark):
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    idgraph1 = get_object_state(a, {})
    idgraph2 = get_object_state(a, {})

    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    idgraph_equal = benchmark(benchmark_idgraph_comparison, idgraph1, idgraph2)

    if pick1 != pick2:
        assert not idgraph_equal
    else:
        assert idgraph_equal

    plt.close('all')


def test_hash_matplotlib():
    """
        Test if idgraph is accurately generated for matplotlib objects
    """
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    hash1 = get_object_hash(a)
    hash2 = get_object_hash(a)
    # init_comparison, hash1 = benchmark(benchmark_hash_ret_comp_hash, a)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are the same
    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    if pick1 != pick2:
        assert hash1.digest() != hash2.digest()
    else:
        assert hash1.digest() == hash2.digest()

    plt.xlabel("XLABEL_2")
    hash3 = get_object_hash(a)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    plt.xlabel("XLABEL_1")
    hash4 = get_object_hash(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert hash1.digest() != hash4.digest()
    else:
        assert hash1.digest() == hash4.digest()

    line = plt.gca().get_lines()[0]
    line_co = line.get_color()
    line.set_color('red')
    hash5 = get_object_hash(a)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash5.digest()

    line.set_color(line_co)
    hash6 = get_object_hash(a)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were the same
    if pick1 != pick2:
        assert hash1.digest() != hash6.digest()
    else:
        assert hash1.digest() == hash6.digest()

    # Close all figures
    plt.close('all')


def test_hash_creation_matplotlib(benchmark):
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    benchmark(benchmark_hash_creation, a)
    assert True
    plt.close('all')


def test_hash_comparison_matplotlib(benchmark):
    plt.close('all')
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    a = plt.plot(df['a'], df['b'])
    plt.xlabel("XLABEL_1")

    hash1 = get_object_hash(a)
    hash2 = get_object_hash(a)

    pick1 = pickle.dumps(a[0])
    pick2 = pickle.dumps(a[0])

    hash_equal = benchmark(benchmark_hash_comparison, hash1, hash2)
    if pick1 != pick2:
        assert not hash_equal
    else:
        assert hash_equal

    plt.close('all')


def test_idgraph_seaborn_displot():
    """
        Test if idgraph is accurately generated for seaborn displot objects (figure-level object)
    """
    # In Python version 3.10.12 and seaborn version 0.13.0, pickled binaries are not equal

    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="hist")
    plot1.set(xlabel="flipper_length_mm")

    idgraph1 = get_object_state(plot1, {})
    idgraph2 = get_object_state(plot1, {})
    # init_comparison, idgraph1 = benchmark(benchmark_idgraph_ret_comp_id, plot1)

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
    idgraph3 = get_object_state(plot1, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set(xlabel="flipper_length_mm")
    idgraph4 = get_object_state(plot1, {})

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    # Close all figures
    plt.close('all')


def test_idgraph_creation_seaborn_displot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="hist")
    plot1.set(xlabel="flipper_length_mm")

    benchmark(benchmark_idgraph_creation, plot1)
    assert True
    plt.close('all')


def test_idgraph_comparison_seaborn_displot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="hist")
    plot1.set(xlabel="flipper_length_mm")

    idgraph1 = get_object_state(plot1, {})
    idgraph2 = get_object_state(plot1, {})

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    idgraph_equal = benchmark(benchmark_idgraph_comparison, idgraph1, idgraph2)
    if pick1 != pick2:
        assert not idgraph_equal
    else:
        assert idgraph_equal

    plt.close('all')


def test_hash_seaborn_displot():
    """
        Test if idgraph is accurately generated for seaborn displot objects (figure-level object)
    """
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    hash1 = get_object_hash(plot1)
    hash2 = get_object_hash(plot1)
    # init_comparison, hash1 = benchmark(benchmark_hash_ret_comp_hash, plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert hash1.digest() != hash2.digest()
    else:
        assert hash1.digest() == hash2.digest()

    plot1.set(xlabel="NEW LABEL")
    hash3 = get_object_hash(plot1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    plot1.set(xlabel="flipper_length_mm")
    hash4 = get_object_hash(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert hash1.digest() != hash4.digest()
    else:
        assert hash1.digest() == hash4.digest()

    # Close all figures
    plt.close('all')


def test_hash_creation_seaborn_displot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    benchmark(benchmark_hash_creation, plot1)
    assert True
    plt.close('all')


def test_hash_comparison_seaborn_displot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.displot(data=df, x="flipper_length_mm",
                        y="bill_length_mm", kind="kde")
    plot1.set(xlabel="flipper_length_mm")

    hash1 = get_object_hash(plot1)
    hash2 = get_object_hash(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    hash_equal = benchmark(benchmark_hash_comparison, hash1, hash2)
    if pick1 != pick2:
        assert not hash_equal
    else:
        assert hash_equal
    plt.close('all')


def test_idgraph_seaborn_scatterplot():
    """
        Test if idgraph is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    # Close all figures
    plt.close('all')

    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    idgraph1 = get_object_state(plot1, {})
    idgraph2 = get_object_state(plot1, {})
    # init_comparison, idgraph1 = benchmark(benchmark_idgraph_ret_comp_id, plot1)

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
    idgraph3 = get_object_state(plot1, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph3

    plot1.set_xlabel('flipper_length_mm')
    idgraph4 = get_object_state(plot1, {})

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert idgraph1 != idgraph4
    else:
        assert idgraph1 == idgraph4

    plot1.set_facecolor('#eafff5')
    idgraph5 = get_object_state(plot1, {})

    # Assert that the id graph changes when the object changes
    assert idgraph1 != idgraph5

    # Close all figures
    plt.close('all')


def test_idgraph_creation_seaborn_scatterplot(benchmark):
    plt.close('all')

    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    benchmark(benchmark_idgraph_creation, plot1)
    assert True
    plt.close('all')


def test_idgraph_comparison_seaborn_scatterplot(benchmark):
    plt.close('all')

    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    idgraph1 = get_object_state(plot1, {})
    idgraph2 = get_object_state(plot1, {})

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    idgraph_equal = benchmark(benchmark_idgraph_comparison, idgraph1, idgraph2)
    if pick1 != pick2:
        assert not idgraph_equal
    else:
        assert idgraph_equal
    plt.close('all')


def test_hash_seaborn_scatterplot():
    """
        Test if idgraph is accurately generated for seaborn scatterplot objects (axes-level object)
    """
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    hash1 = get_object_hash(plot1)
    hash2 = get_object_hash(plot1)
    # init_comparison, hash1 = benchmark(benchmark_hash_ret_comp_hash, plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    # Assert that the id graph does not change when the object remains unchanged if pickle binaries are same
    if pick1 != pick2:
        assert hash1.digest() != hash2.digest()
    else:
        assert hash1.digest() == hash2.digest()

    plot1.set_xlabel('Flipper Length')
    hash3 = get_object_hash(plot1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash3.digest()

    plot1.set_xlabel('flipper_length_mm')
    hash4 = get_object_hash(plot1)

    # Assert that the original id graph is restored when the original object state is restored if pickle binaries were same
    if pick1 != pick2:
        assert hash1.digest() != hash4.digest()
    else:
        assert hash1.digest() == hash4.digest()

    plot1.set_facecolor('#eafff5')
    hash5 = get_object_hash(plot1)

    # Assert that the id graph changes when the object changes
    assert hash1.digest() != hash5.digest()

    # Close all figures
    plt.close('all')


def test_hash_creation_seaborn_scatterplot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    benchmark(benchmark_hash_creation, plot1)
    assert True
    plt.close('all')


def test_hash_comparison_seaborn_scatterplot(benchmark):
    plt.close('all')
    df = sns.load_dataset('penguins')
    plot1 = sns.scatterplot(data=df, x="flipper_length_mm", y="bill_length_mm")
    plot1.set_xlabel('flipper_length_mm')
    plot1.set_facecolor('white')

    hash1 = get_object_hash(plot1)
    hash2 = get_object_hash(plot1)

    pick1 = pickle.dumps(plot1)
    pick2 = pickle.dumps(plot1)

    hash_equal = benchmark(benchmark_hash_comparison, hash1, hash2)
    if pick1 != pick2:
        assert not hash_equal
    else:
        assert hash_equal
    plt.close('all')
