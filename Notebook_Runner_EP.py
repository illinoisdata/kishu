from nbloader import Notebook
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read, write
from jupyter_client import KernelManager
from nbformat.v4 import new_code_cell
import sys
import os
import pickle


class NotebookRunner:
    def __init__(self, test_notebook):
        self.test_notebook = test_notebook
        self.path_to_notebook = os.getcwd()
        self.pickle_file = "pickle_" + os.path.splitext(test_notebook)[0]
        sys.path.append(os.path.abspath('../../'))
        
        # Get the path to the parent folder
        self.outer_path = os.path.abspath(os.path.join(os.getcwd(), '../../'))
        
        
    
    def execute(self, cell_indices, objects):
        with open(self.test_notebook) as nb_file:
            nb = read(nb_file, as_version=4)
            

        # Create a new notebook object containing only the specified cells
        new_nb = nb.copy()
        new_nb.cells = [nb.cells[i] for i in cell_indices]
        
        #Make dictionary and then pickle that into a file
        
        code = '''my_list = {}
    fout = open('{}', 'wb')'''.format(objects, self.pickle_file) 
        code = '\n'.join(line[4:] if line.startswith('    ') else line for line in code.split('\n'))
        
        code_two = "test = locals()\nresult_dict = {var: test[var] for var in my_list}\npickle.dump(result_dict, fout)\nprint(result_dict)\nfout.close()"
        
        
        # create a new code cell
        new_cell = new_code_cell(source=code)
        new_cell_two = new_code_cell(source=code_two)

        # add the new cell to the notebook
        nb.cells.append(new_cell)
        nb.cells.append(new_cell_two)


        # Execute the notebook cells
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': self.path_to_notebook}})
        
        #get the output dictionary
        with open(self.pickle_file, 'rb') as file:
            data = pickle.load(file)
        return data

#         # Write the executed notebook to a new file
#         new_notebook_path = os.path.join(self.path_to_notebook, 'Output_20230510.ipynb')
#         with open(new_notebook_path, mode='wt') as f:
#             write(nb, f)