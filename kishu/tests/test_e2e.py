import os
import dill

from kishu.nbexec import NotebookRunner


NB_LIST_TEST = [
    'simple.ipynb',
    'numpy.ipynb'
]


# These take a very long time to run; only run locally and not on Github actions.
NB_LIST_REAL = [
    'ml-ex1.ipynb',
    '04_training_linear_models.ipynb',
    'sklearn_tweet_classification.ipynb'
]


def test_real_notebooks_end_to_end_checkout(num_iters_per_notebook=3, nb_list=NB_LIST_TEST, nb_dir="tests/real_notebooks"):
    """
        Tests checkout correctness by comparing namespace contents at cell execution X in the middle of a notebook,
        and namespace contents after checking out cell execution X completely executing the notebook.
        X is randomly generated (nbexec.py), and this test can be repeated multiple times for each notebook with
        different X values to increase robustness.

        @param num_iters_per_notebook: number of times this test is ran for each notebook.
        @param nb_list: list of notebooks to run this test for.
        @param nb_dir: name of directory containing test notebooks.
    """
    for notebook_name in nb_list:
        for _ in range(num_iters_per_notebook):
            # Open notebook.
            path_to_notebook = os.getcwd()
            notebook = NotebookRunner(path_to_notebook + "/" + nb_dir + "/" + notebook_name)

            # Get notebook namespace contents at cell execution X and contents after checking out cell execution X.
            namespace_before_checkout, namespace_after_checkout = notebook.execute_e2e_random_test()

            # The contents should be identical.
            assert namespace_before_checkout.keys() == namespace_after_checkout.keys()
            for key in namespace_before_checkout.keys():
                # As certain classes don't have equality (__eq__) implemented, we compare serialized bytestrings.
                assert dill.dumps(namespace_before_checkout[key]) == dill.dumps(namespace_after_checkout[key])
