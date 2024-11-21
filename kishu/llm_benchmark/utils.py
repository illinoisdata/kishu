import os
import re
import tempfile

import nbformat.v4
from nbformat import NotebookNode


def check_file_exist(data: list[str]) -> bool:
    # check if all file in data list exists
    all_files_exist = True
    for file in data:
        if not os.path.exists(file):
            all_files_exist = False
            break
    return all_files_exist


def get_cell_code(content: str) -> str:
    code_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)
    if not code_blocks:
        raise ValueError("No Python code blocks found in the text.")

    # Combine all code blocks into a single string
    combined_code = "\n\n".join(block.strip() for block in code_blocks)
    return combined_code



def append_cell(nb_file: NotebookNode, cell_code: str) -> None:
    # append cell_code to nb_file
    cell = nbformat.v4.new_code_cell(cell_code)
    nb_file.cells.append(cell)


def copy_cell(new_nb_file: NotebookNode, old_nb_file: NotebookNode, copy_until: int) -> None:
    # copy cells from old_nb_file to new_nb_file, copy until cell "copy_until"(included)
    new_nb_file.cells = old_nb_file.cells[:copy_until + 1]


def create_tmp_ipynb_in_current_dir():
    # Get the current directory
    current_dir = os.getcwd()

    # Create a temporary file with .ipynb extension in the current directory
    with tempfile.NamedTemporaryFile(dir=current_dir, suffix=".ipynb", delete=False) as tmp_file:
        tmp_file_name = tmp_file.name
        print(f"Temporary .ipynb file created: {tmp_file_name}")

    # Return the temporary file name
    return tmp_file_name