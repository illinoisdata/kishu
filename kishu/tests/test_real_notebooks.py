import json
import os
import shutil
from tempfile import NamedTemporaryFile, gettempdir
import dill

import nbformat
from typing import Any
from kishu.checkpoint_io import init_checkpoint_database
from kishu.jupyterint2 import CommitEntry
from kishu.nbexec import NotebookRunner
from kishu.plan import ExecutionHistory

nb_list = ['real_notebooks/numpy.ipynb', 'real_notebooks/ml-ex1.ipynb']


def test_real_notebooks():
    cell_indices = []
    path_to_notebook = os.getcwd()
    notebook_name = "real_notebooks/numpy-Copy1.ipynb"
    vals = ['knn']
    notebook = NotebookRunner(path_to_notebook + "/tests/" + notebook_name)
    output = notebook.execute(cell_indices, vals)

    expected_output_knn = dill.load(open(path_to_notebook + '/tests/real_notebooks/dill_storage/numpy.ipynb', 'rb'))
    assert dill.dumps(output['knn']) == dill.dumps(expected_output_knn)


def random_test_real_notebooks():
    for notebook_name in nb_list:
        # Open notebook
        path_to_notebook = os.getcwd()
        notebook = NotebookRunner(path_to_notebook + "/" + notebook_name)

        # get dumped notebook session
        output1, output2 = notebook.execute_and_compare()

        print(output1.keys())
        print(output2.keys())
        assert output1.keys() == output2.keys()
        #print(output2["kishu_log"])
        for key in output1.keys():
            # file handler which we added to store items in the notebook. Skip.
            if key in ["kishu_log", "fout", "result_dict", "exceptions", "test"]:
                continue
            print(key)
            if dill.dumps(output1[key]) != dill.dumps(output2[key]):
                print(dill.dumps(output1[key]))
                print(dill.dumps(output2[key]))
            assert(dill.dumps(output1[key]) == dill.dumps(output2[key]))

random_test_real_notebooks()

