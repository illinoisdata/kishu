import datetime
import json
import requests
import subprocess
import time
import uuid
import websocket

from pathlib import Path
from requests.adapters import HTTPAdapter
from typing import Any, Dict, Optional
from urllib3.util import Retry

from kishu.jupyter.runtime import JupyterRuntimeEnv


class NotebookHandler:
    # Number of seconds to wait on kernel connection.
    CONNECTION_TIMEOUT = 5

    # Number of seconds to wait on receiving output from cell executions.
    CELL_EXECUTION_TIMEOUT = 600
    """
        Class for running notebook code in Jupyter Sessions hosted in Jupyter Notebook servers.
    """
    def __init__(self, server_url: str, header: Dict[str, Any], kernel_id: str, session_id: str, persist: bool = False):
        self.server_url = server_url
        self.kernel_id = kernel_id
        self.session_id = session_id
        self.request_url = self.server_url.replace("http", "ws") + f"/api/kernels/{self.kernel_id}/channels"
        self.header = header
        self.persist = persist  # Some tests require us to not kill jupyter server, so this controlls whether we do or not
        self.websocket: Optional[websocket.WebSocket] = None

    def __enter__(self):
        self.websocket = websocket.create_connection(self.request_url, header=self.header,
                                                     timeout=NotebookHandler.CONNECTION_TIMEOUT,
                                                     close_timeout=NotebookHandler.CONNECTION_TIMEOUT)
        self.websocket.settimeout(NotebookHandler.CELL_EXECUTION_TIMEOUT)
        return self

    @staticmethod
    def send_execute_request(code: str, silent: bool):
        msg_type = 'execute_request'
        content = {'code': code, 'silent': silent}
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

    def _read_notebook_output(self, terminate_msg_type: str, output_msg_type: str = "") -> str:
        if self.websocket is None:
            raise RuntimeError("Websocket is not initialized")

        output = ""
        try:
            msg_type = ""
            while msg_type != terminate_msg_type:
                rsp = json.loads(self.websocket.recv())
                msg_type = rsp["msg_type"]
                if msg_type == output_msg_type:
                    output += rsp["content"]["text"]
        except TimeoutError:
            print("Cell execution timed out.")

        return output

    def run_code(self, cell_code: str, silent: bool = False) -> str:
        if self.websocket is None:
            raise RuntimeError("Websocket is not initialized")

        # Execute cell code
        self.websocket.send(json.dumps(NotebookHandler.send_execute_request(cell_code, silent)))

        # There's no output if silent is true
        if silent:
            return self._read_notebook_output("execute_reply")

        # Read cell output. The first read_notebook_output is for ensuring that the input has been read.
        self._read_notebook_output("execute_input")
        return self._read_notebook_output("status", "stream")

    def __exit__(self, exception_type, exception_value, traceback):
        if self.websocket is not None:
            try:
                self.websocket.close()
            except TimeoutError:
                print("Connection close timed out.")

        if not self.persist:
            # Shutdown the kernel
            kernel_delete_url = f"{self.server_url}/api/kernels/{self.kernel_id}"
            requests.delete(kernel_delete_url, headers=self.header)

            # Delete the session
            session_delete_url = f"{self.server_url}/api/sessions/{self.session_id}"
            requests.delete(session_delete_url, headers=self.header)


class JupyterServerRunner:
    """
        Class for running Jupyter Notebook server processes. Used for hosting Jupyter Sessions,
        which are in turn used to execute notebooks.
        Used for end-to-end testing in combination with Kishu commands.
    """

    # Maximum number of retries each connection is attempted.
    MAX_RETRIES = 100

    # Base sleep time between consecutive retries.
    SLEEP_TIME = 0.1

    # Adapter defining retry strategy for get/post requests.
    ADAPTER = HTTPAdapter(max_retries=Retry(total=MAX_RETRIES,
                                            backoff_factor=SLEEP_TIME,
                                            allowed_methods=frozenset(['GET', 'POST'])))

    def __init__(self, server_ip: str = "127.0.0.1", port: str = "10000", server_token: str = "abcdefg"):
        self.server_ip = server_ip
        self.port = port
        self.server_token = server_token

        # Header for sending requests to the server.
        self.header: Dict[str, Any] = {'Authorization': f"Token {server_token}"}

        # Server process for communication with the server.
        self.server_process: Optional[subprocess.Popen] = None

        # The URL of the Jupyter Notebook Server. Note that the actual port may be different from the specified port
        # as the latter may be in use.
        self.server_url: str = ""

    def __enter__(self):
        """
        Initialize a JupyterServerRunner instance.

        Args:
            server_ip (str): IP address to start the server at.
            port (str): port to connect to the server with.
            server_token (str): token to connect to the server with for user authentication.
        """
        command = (
            f"jupyter notebook --allow-root --no-browser --ip={self.server_ip} --port={self.port} "
            f"--ServerApp.disable_check_xsrf=True --NotebookApp.token='{self.server_token}'"
        )

        # Start the Jupyter Server process and get its URL.
        self.server_process = subprocess.Popen(command.split(), shell=False,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.server_url = self.get_server_url()

        return self

    def get_server_url(self) -> str:
        if self.server_process is None:
            raise RuntimeError("The Jupyter Server is not initialized yet.")

        for _ in range(JupyterServerRunner.MAX_RETRIES):
            time.sleep(JupyterServerRunner.SLEEP_TIME)
            for server in JupyterRuntimeEnv.iter_maybe_running_servers():
                if server["pid"] == self.server_process.pid:
                    return server["url"][:-1]
        raise TimeoutError("server connection timed out")

    def start_session(self, notebook_path: Path, kernel_name: str = "python3", persist: bool = False) -> NotebookHandler:
        """
        Create a notebook session backed by the specified notebook file on disk. Returns the ID of the newly
        started kernel.

        Args:
            notebook_path (Path): path to notebook file.
            kernel_name (str): Python kernel version to use.
        """
        if self.server_process is None:
            raise RuntimeError("The Jupyter Server is not initialized yet.")

        request_url = self.server_url + "/api/sessions"
        create_session_data = {"kernel": {"name": kernel_name}, "name": notebook_path.name, "type": "notebook",
                               "path": str(notebook_path)}

        with requests.Session() as session:
            session.mount('http://', JupyterServerRunner.ADAPTER)
            response = requests.post(request_url, headers=self.header, data=json.dumps(create_session_data))
            response_json = json.loads(response.text)

            # Extract kernel id and establish connection with the kernel.
            session_id = response_json["id"]
            kernel_id = response_json["kernel"]["id"]
            return NotebookHandler(self.server_url, self.header, kernel_id, session_id, persist)

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Shuts down the Jupyter server.
        """
        if self.server_process is not None:
            self.server_process.terminate()

            # process is still alive; kill it.
            if self.server_process.poll() is None:
                self.server_process.kill()
