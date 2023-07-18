"""
nbexec - Notebook Runner

This module provides a NotebookRunner class for extracting values from cells in a Jupyter notebook.

Classes:
- NotebookRunner: Executes cells in a Jupyter notebook, returns output as a dictionary.

Usage:
1. Create an instance of NotebookRunner, providing the path to the notebook to execute.
2. Use the 'execute' method to specify the cell indices and var_names for the resulting dictionary.
3. 'execute' method runs cells, captures output, and returns result as dictionary.


Dependencies:
- nbconvert: Library for executing Jupyter notebook cells.
- nbformat: Library for working with Jupyter notebook file format.
"""
import os
import pickle
import re
import subprocess
from typing import List

import requests
from IPython.display import display
from jupyter_client import KernelManager
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read
from nbformat.v4 import new_code_cell


class Kernel:
    """
    Executes specified commands for a specific notebooks in a defined jupyter notebook instance

    Args:
        token (str): Token for the matching notebook.
    """

    def __init__(self):
        """
        Initialize a NotebookRunner instance.

        Args:
            token (str): Token for the matching notebook.
        """
        runtime_command = "jupyter --runtime-dir"
        runtime_output = subprocess.check_output(runtime_command, shell=True)
        runtime_dir = runtime_output.decode("utf-8")
        self.runtime_dir = runtime_dir

    def get_notebooks(self):
        """
        Get the running notebooks for each server.

        Returns:
            dict: Dictionary with server addresses as keys and associated running notebooks as values.
        """
        notebook_servers = {}
        notebook_command = "jupyter notebook list"
        notebook_output = subprocess.check_output(notebook_command, shell=True)
        notebook_string = notebook_output.decode("utf-8").strip()
        lines = notebook_string.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("http://"):
                server_address = line.split("::")[0].strip()
                curr_token = line.split("?token=")[1].split("::")[0].strip()
                curr_notebook = re.findall(r"http://localhost:\d+", server_address)[0]
                curr_port = re.search(r"http://localhost:(\d+)", curr_notebook).group(1)
                notebook_servers[curr_port] = []
                headers = {"Authorization": f"token {curr_token}"}
                response = requests.get(
                    f"{curr_notebook}/api/sessions", headers=headers
                )
                if response.status_code == 200:
                    running_notebooks = response.json()
                    # Just get the path and then add the portname at the end
                    for notebook in running_notebooks:
                        notebook_path = notebook.get("notebook", {}).get("path")
                        notebook_kernel = notebook["kernel"]["id"]
                        inp = (notebook_path, notebook_kernel)
                        notebook_servers[curr_port].append(inp)

        return notebook_servers

    def send_cmd(self, port: str, filepath: str, command: str):
        """
        Send a command and save the output to a file.

        Args:
            filename (str): Name of the file to save the command output.
            command (str): Command to execute.
        """

        # Get running notebooks
        notebooks = self.get_notebooks()
        print("notebooks", notebooks)
        kernel_id = ""
        for server_port, notebook_info_list in notebooks.items():
            if server_port == port:
                for notebook_info in notebook_info_list:
                    notebook_path, curr_kernel = notebook_info
                    if notebook_path == filepath:
                        kernel_id = curr_kernel

        # Get the kernel ID
        terminal_command = "ls -tr " + self.runtime_dir
        runtime_list = subprocess.check_output(terminal_command, shell=True)
        runtimes = runtime_list.decode("utf-8")
        matching_line = next(
            (line.strip() for line in runtimes.split("\n") if kernel_id in line), None
        )
        if matching_line:
            notebook_kernel = (
                self.runtime_dir.rstrip("\n") + "/" + matching_line.rstrip("\n")
            )
        else:
            return

        # Execute the command
        km = KernelManager()
        km.load_connection_file(notebook_kernel)
        km.connect_iopub()
        client = km.client()
        client.start_channels()
        return client.execute_interactive(command)


kernel = Kernel()
test_one = kernel.send_cmd("8888", "testNotebook.ipynb", "x = 10")
test_two = kernel.send_cmd("8888", "Desktop/TestNotebook.ipynb", "x = 6")
test_three = kernel.send_cmd("8889", "testNotebook.ipynb", "x = 6")
