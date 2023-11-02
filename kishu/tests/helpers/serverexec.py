import datetime
import json
import os
import requests
import subprocess
import time
import uuid

from requests.adapters import HTTPAdapter
from typing import Any, Dict, List, Optional
from urllib3.util import Retry
from websocket import create_connection, WebSocketTimeoutException
from websocket._core import WebSocket

from kishu.runtime import _iter_maybe_running_servers


def send_execute_request(cell_code: str) -> Dict:
    """
    Helper for formatting the JSON payload for code execution requests to send to Jupyter Notebook kernels.

    Args:
        cell_code (str): cell code to run.
    """
    msg_type = 'execute_request'
    content = {'code': cell_code, 'silent': False}
    hdr = {'msg_id': uuid.uuid1().hex,
           'username': 'test',
           'session': uuid.uuid1().hex,
           'data': datetime.datetime.now().isoformat(),
           'msg_type': msg_type,
           'version': '5.0'}
    msg = {'header': hdr, 'parent_header': hdr,
           'metadata': {},
           'content': content}
    return msg


class NotebookHandler:
    """
        Class for running notebook code in Jupyter Sessions hosted in Jupyter Notebook servers.
    """
    def __init__(self, request_url: str, header: Dict[str, Any]):
        self.request_url: str = request_url
        self.header: Dict[str, Any] = header
        self.kernel_conn: Optional[WebSocket] = None

    def __enter__(self):
        self.kernel_conn = create_connection(self.request_url, header=self.header)
        return self

    def run_code(self, cell_code: str) -> str:
        if self.kernel_conn is None:
            raise RuntimeError("Kernel connection has not been initialized yet.")

        self.kernel_conn.send(json.dumps(send_execute_request(cell_code)))

        # Read the output of the cell execution.
        cell_output = ""
        try:
            msg_type = ''
            while msg_type != "execute_input":
                rsp = json.loads(self.kernel_conn.recv())
                msg_type = rsp["msg_type"]
            msg_type = ''
            while msg_type != "status":
                rsp = json.loads(self.kernel_conn.recv())
                msg_type = rsp["msg_type"]
                if msg_type == "stream":
                    cell_output = rsp["content"]["text"]
        except WebSocketTimeoutException:
            raise WebSocketTimeoutException("Cell execution timed out.")

        return cell_output

    def __exit__(self, exception_type, exception_value, traceback):
        if self.kernel_conn is not None:
            self.kernel_conn.close()


class JupyterServerRunner:
    """
        Class for running Jupyter Notebook server processes. Used for hosting Jupyter Sessions,
        which are in turn used to execute notebooks.
        Used for end-to-end testing in combination with Kishu commands.
    """

    # Maximum number of retries each connection is attempted.
    MAX_RETRIES = 50

    # Base sleep time between consecutive retries.
    SLEEP_TIME = 0.1

    # Adapter defining retry strategy for get/post requests.
    ADAPTER = HTTPAdapter(max_retries=Retry(total=MAX_RETRIES,
                                            backoff_factor=SLEEP_TIME,
                                            allowed_methods=frozenset(['GET', 'POST'])))

    def __enter__(self, server_ip: str = "127.0.0.1", port: str = "10000", server_token: str = "abcdefg"):
        """
        Initialize a JupyterServerRunner instance.

        Args:
            server_ip (str): IP address to start the server at.
            port (str): port to connect to the server with.
            server_token (str): token to connect to the server with for user authentication.
        """
        self.server_ip = server_ip
        self.port = port
        self.server_token = server_token

        # Header for sending requests to the server.
        self.header: Dict[str, Any] = {'Authorization': f"Token {server_token}"}

        # Server process for communication with the server.
        command = f"""jupyter notebook --allow-root --no-browser --ip={self.server_ip} --port={self.port}
            --ServerApp.disable_check_xsrf=True --NotebookApp.token='{self.server_token}'"""

        self.server_process: subprocess.Popen = subprocess.Popen(command.split(), shell=False,
                                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # The URL of the Jupyter Notebook Server. Note that the actual port may be different from the specified port
        # as the latter may be in use.
        self.server_url: str = self.get_server_url()

        # Connections to kernels in the server.
        self.kernel_connections: Dict[str, NotebookHandler] = {}

        return self

    def get_server_url(self) -> str:
        for _ in range(JupyterServerRunner.MAX_RETRIES):
            time.sleep(JupyterServerRunner.SLEEP_TIME)
            for server in _iter_maybe_running_servers():
                if server["pid"] == self.server_process.pid:
                    return server["url"][:-1]
        raise TimeoutError("server connection timed out")

    def get_notebook_contents(self, notebook_dir: str, notebook_name: str) -> List[str]:
        """
        Gets and returns the cell code of a notebook by reading it server-side.

        Args:
            notebook_dir (str): directory of notebook file relative to Jupyter Server's root.
            notebook_name (str): name of the notebook file.
        """
        request_url = self.server_url + f"/api/contents/{os.path.join(notebook_dir, notebook_name)}"

        # Send request to read notebook to server
        with requests.Session() as session:
            session.mount('http://', JupyterServerRunner.ADAPTER)
            response = requests.get(request_url, headers=self.header)
            response_json = json.loads(response.text)
            assert response_json['name'] == notebook_name

            # Extract code from notebook
            return [c['source'] for c in response_json['content']['cells']]

    def start_session(self, notebook_dir: str, notebook_name: str, kernel_name: str = "python3") -> NotebookHandler:
        """
        Create a notebook session backed by the specified notebook file on disk. Returns the ID of the newly
        started kernel.

        Args:
            notebook_dir (str): directory of notebook file relative to Jupyter Server's root.
            notebook_name (str): name of the notebook file.
            kernel_name (str): Python kernel version to use.
        """
        request_url = self.server_url + "/api/sessions"
        create_session_data = {"kernel": {"name": kernel_name}, "name": notebook_name, "type": "notebook",
                               "path": os.path.join(notebook_dir, notebook_name)}

        with requests.Session() as session:
            session.mount('http://', JupyterServerRunner.ADAPTER)
            response = requests.post(request_url, headers=self.header, data=json.dumps(create_session_data))
            response_json = json.loads(response.text)

            # Extract kernel id and establish connection with the kernel.
            kernel_id = response_json["kernel"]["id"]
            request_url = self.server_url.replace("http", "ws") + f"/api/kernels/{kernel_id}/channels"
            return NotebookHandler(request_url, self.header)

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Shuts down the Jupyter server.
        """
        if self.server_process is not None:
            self.server_process.terminate()

            # process is still alive; kill it.
            if self.server_process.poll() is None:
                self.server_process.kill()
