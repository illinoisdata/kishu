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

    def __init__(self, token: str):
        """
        Initialize a NotebookRunner instance.

        Args:
            token (str): Token for the matching notebook.
        """
        self.token = token

        runtime_command = "jupyter --runtime-dir"
        runtime_output = subprocess.check_output(runtime_command, shell=True)
        runtime_dir = runtime_output.decode("utf-8")
        self.runtime_dir = runtime_dir

        notebook_command = "jupyter notebook list"
        notebook_output = subprocess.check_output(notebook_command, shell=True)
        notebook_string = notebook_output.decode("utf-8")
        matching_notebook = None
        lines = notebook_string.split("\n")
        for line in lines:
            if self.token in line:
                matching_notebook = re.findall(r"http://localhost:\d+", line)
                break
        if matching_notebook:
            self.notebook_url = matching_notebook[0]
        else:
            print("No matching notebook found.")

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
                token = line.split("?token=")[1].split("::")[0].strip()
                curr_notebook = re.findall(r"http://localhost:\d+", server_address)[0]
                curr_port = re.search(r"http://localhost:(\d+)", curr_notebook).group(1)
                notebook_servers[server_address] = []
                headers = {"Authorization": f"token {token}"}
                response = requests.get(
                    f"{curr_notebook}/api/sessions", headers=headers
                )
                if response.status_code == 200:
                    running_notebooks = response.json()
                    for notebook in running_notebooks:
                        notebook_path = notebook.get("notebook", {}).get("path")
                        notebook_name = os.path.basename(notebook_path)
                        notebook_name_with_port = f"{notebook_name} ({curr_port})"
                        notebook_servers[server_address].append(notebook_name_with_port)

        return notebook_servers

    def send_cmd(self, filename: str, command: str):
        """
        Send a command and save the output to a file.

        Args:
            filename (str): Name of the file to save the command output.
            command (str): Command to execute.
        """

        # Get request to obtain running notebooks
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(f"{self.notebook_url}/api/sessions", headers=headers)
        if response.status_code == 200:
            running_notebooks = response.json()
            # Search for the notebook with the desired name
            for notebook in running_notebooks:
                if notebook.get("notebook", {}).get("path") == filename:
                    kernel_id = notebook.get("kernel", {}).get("id")
                    break
            else:
                print(f"No running notebook found with the filename: {filename}")
                return
        else:
            print("Failed to retrieve the list of running notebooks.")
            return

        # Get the kernel ID
        terminal_command = "ls -tr /Users/shriyangosavi/Library/Jupyter/runtime/"
        runtime_list = subprocess.check_output(terminal_command, shell=True)
        runtimes = runtime_list.decode("utf-8")
        matching_line = next(
            (line.strip() for line in runtimes.split("\n") if kernel_id in line), None
        )
        if matching_line:
            kernel = self.runtime_dir.rstrip("\n") + "/" + matching_line.rstrip("\n")
        else:
            print("No matching line found.")
            return

        # Execute the command
        km = KernelManager()
        km.load_connection_file(kernel)
        km.connect_iopub()
        client = km.client()
        client.start_channels()
        return client.execute_interactive(command)


token = "40e27364aa593de54495a582fe7db71dceee0c4d883898ba"
kernel = Kernel(token)
# print(kernel.send_cmd("testNotebook.ipynb", "x = 20"))
print(kernel.get_notebooks())
