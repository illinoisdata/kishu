import dill
import nbformat
import pytest
import os
import shutil
import random
import time
import gc

from typing import List
from pathlib import Path, PurePath

from kishu.jupyterint import KishuForJupyter
from kishu.storage.config import Config

from tests.helpers.nbexec import NotebookRunner

NOTEBOOK_DIR = "tests/notebooks/"
TMP_DIR = "notebooks/"


def set_notebook_path_env(notebook_path):
    os.environ["TEST_NOTEBOOK_PATH"] = str(Path(notebook_path).resolve())
    os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE] = "true"

def run_test(notebook_path, cell_num_to_restore: int, enable_incremental_store):
    """
    Tests checkout correctness by comparing namespace contents at cell_num_to_restore in the middle of a notebook,
    and namespace contents after checking out cell_num_to_restore completely executing the notebook.
    """
    tmp_nb_path = "/data/elastic-notebook/tmp/" + TMP_DIR + str(random.randint(0, 9999999)) + notebook_path
    try:
        os.remove(tmp_nb_path)
    except OSError:
        pass
    shutil.copy(NOTEBOOK_DIR + notebook_path, tmp_nb_path)

    try:
        set_notebook_path_env(tmp_nb_path)
        Config.set('PLANNER', 'incremental_cr', False)
        Config.set('EXPERIMENT', 'record_results', True)
        Config.set('EXPERIMENT', 'notebook_name', notebook_path)
        Config.set('EXPERIMENT', 'csv_path', '/data/elastic-notebook/tmp/kishu_results.csv')
        Config.set('EXPERIMENT', 'method', f'kishu_incremental_{str(enable_incremental_store)}')
        notebook = NotebookRunner(tmp_nb_path)

    # Get notebook namespace contents at cell execution X and contents after checking out cell execution X.
    
        namespace_before_checkout, namespace_after_checkout = notebook.execute_full_checkout_test(cell_num_to_restore)
    except Exception as e:
        print(e)

    try:
        os.remove(tmp_nb_path)
    except OSError:
        pass

    # # The contents should be identical.
    # assert namespace_before_checkout.keys() == namespace_after_checkout.keys()
    # for key in namespace_before_checkout.keys():
    #     # As certain classes don't have equality (__eq__) implemented, we compare serialized bytestrings.
    #     assert dill.dumps(namespace_before_checkout[key]) == dill.dumps(namespace_after_checkout[key])


def run_dill_test(notebook_path, cell_num_to_restore: int):
    start = time.time()
    try:
        notebook = NotebookRunner(NOTEBOOK_DIR + notebook_path, notebook_path)
        notebook.execute_dill_test(cell_num_to_restore)
    except Exception as e:
        print(e)
    print("total time:", time.time() - start)


def run_criu_test(notebook_path, incremental_dump, cell_num_to_restore: int):
    start = time.time()
    try:
        notebook = NotebookRunner(NOTEBOOK_DIR + notebook_path, notebook_path)
        notebook.execute_criu_test(cell_num_to_restore, incremental_dump)
    except Exception as e:
        print(e)
    print("total time:", time.time() - start)

    default_n_threads = 8
    os.environ['OPENBLAS_NUM_THREADS'] = f"{default_n_threads}"
    os.environ['MKL_NUM_THREADS'] = f"{default_n_threads}"
    os.environ['OMP_NUM_THREADS'] = f"{default_n_threads}"
    

if __name__ == "__main__":
    for nb, cell in [
        #('bruteforce-clustering.ipynb', 16),  # great, 400M
        #('building-an-asset-trading-strategy.ipynb', 25),
        #('model-stacking-feature-engineering-and-eda.ipynb', 69),  # great, 400M
        # ('nlp-glove-bert-tf-idf-lstm-explained.ipynb', 67),  # doesn't work
        # ('04_training_linear_models.ipynb', 80),
        # ('ml-ex3.ipynb', 10),
        #('basic-eda-cleaning-and-glove.ipynb', 37),  # not good
        # ('agricultural-drought-prediction.ipynb', 10),
        #('store-sales-ts-forecasting-a-comprehensive-guide.ipynb', 35),  # great, 400M 
        #('sklearn_tweet_classification.ipynb', 42),  # not good
        #('tps-mar-fast-workflow-using-scikit-learn-intelex.ipynb', 43),  # great, 200M
        # ('time-series-forecasting-with-prophet.ipynb', 26)  # doesn't work
        #('pyspark.ipynb', 35)
        ('ray.ipynb', 9)
    ]:
        default_n_threads = 8
        os.environ['OPENBLAS_NUM_THREADS'] = f"{default_n_threads}"
        os.environ['MKL_NUM_THREADS'] = f"{default_n_threads}"
        os.environ['OMP_NUM_THREADS'] = f"{default_n_threads}"
        print("run test:", nb)
        #run_test(nb, cell, True)
        #run_test(nb, cell, False)
        run_dill_test(nb, cell)
