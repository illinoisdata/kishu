import sys
import os.path

# Append the relative path to the parent folder (elastic-notebook)
sys.path.append(os.path.abspath('../../'))

from Notebook_Runner_EP import NotebookRunner

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def test_notebookrunner_basic(): 
    cell_indices = [0, 1, 2, 3]
    objects = ['z', 'b', 'a']
    notebook = NotebookRunner('test_basic.ipynb')
    output = notebook.execute(cell_indices, objects)
    assert (output == {'z': 2, 'b': 9, 'a': 1})