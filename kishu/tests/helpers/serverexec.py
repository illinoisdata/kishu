import datetime
import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
import websocket
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from kishu.jupyter.runtime import JupyterRuntimeEnv


class CellExecutionError(Exception):
    def __init__(self, cell_code: str, traceback: str):
        super().__init__(f"Error while executing...\n\n{cell_code}\n\n...with traceback:\n\n{traceback}")


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
        self.websocket = websocket.create_connection(
            self.request_url,
            header=self.header,
            timeout=NotebookHandler.CONNECTION_TIMEOUT,
            close_timeout=NotebookHandler.CONNECTION_TIMEOUT,
        )
        self.websocket.settimeout(NotebookHandler.CELL_EXECUTION_TIMEOUT)
        return self

    @staticmethod
    def make_execute_request(code: str, silent: bool):
        msg_id = str(uuid.uuid4())
        msg_type = "execute_request"
        content = {"code": code, "silent": silent}
        hdr = {
            "msg_id": msg_id,
            "username": "test",
            "session": str(uuid.uuid4()),
            "data": datetime.datetime.now().isoformat(),
            "msg_type": msg_type,
            "version": "5.0",
        }
        req = {"header": hdr, "parent_header": hdr, "metadata": {}, "content": content}
        return req, msg_id

    def run_code(self, cell_code: str, silent: bool = False) -> Tuple[str, str]:
        if self.websocket is None:
            raise RuntimeError("Websocket is not initialized")

        # Execute cell code.
        req, msg_id = NotebookHandler.make_execute_request(cell_code, silent)
        self.websocket.send(json.dumps(req))

        # Read output.
        stream_output = ""
        data_output = ""
        try:
            while True:
                # Only listen to relevant message.
                msg = json.loads(self.websocket.recv())
                if msg["parent_header"].get("msg_id") != msg_id:
                    continue

                # Accumulate output.
                msg_type = msg["header"]["msg_type"]
                content = msg["content"]
                if msg_type == "stream":
                    stream_output += content["text"]
                elif msg_type in ("display_data", "execute_result"):
                    data_output += content["data"].get("text/plain", "")
                elif msg_type == "error":
                    traceback = "\n".join(content["traceback"])
                    raise CellExecutionError(cell_code, traceback)

                # Stopping criteria.
                if msg_type == "status" and content["execution_state"] == "idle":
                    break
        except TimeoutError:
            print("Cell execution timed out.")

        return stream_output, data_output

    def __exit__(self, exception_type, exception_value, traceback):
        if self.websocket is not None:
            try:
                self.websocket.close()
            except TimeoutError:
                print("Connection close timed out.")

        if not self.persist:
            # Shutdown the kernel and session
            with requests.Session() as session:
                session.mount("http://", JupyterServerRunner.ADAPTER)
                requests.delete(
                    f"{self.server_url}/api/kernels/{self.kernel_id}",
                    headers=self.header,
                )
                requests.delete(
                    f"{self.server_url}/api/sessions/{self.session_id}",
                    headers=self.header,
                )


class JupyterServerRunner:
    """
    Class for running Jupyter Notebook server processes. Used for hosting Jupyter Sessions,
    which are in turn used to execute notebooks.
    Used for end-to-end testing in combination with Kishu commands.
    """

    # Maximum number of retries each connection is attempted.
    MAX_RETRIES = 200

    # Base sleep time between consecutive retries.
    SLEEP_TIME = 0.1

    # Adapter defining retry strategy for get/post requests.
    ADAPTER = HTTPAdapter(
        max_retries=Retry(total=MAX_RETRIES, backoff_factor=SLEEP_TIME, allowed_methods=frozenset(["GET", "POST"]))
    )

    def __init__(self, server_ip: str = "127.0.0.1", server_token: str = "abcdefg"):
        self.server_ip = server_ip
        self.server_token = server_token

        # Header for sending requests to the server.
        self.header: Dict[str, Any] = {"Authorization": f"Token {server_token}"}

        # Server process for communication with the server.
        self.server_process: Optional[subprocess.Popen] = None

        # The URL of the Jupyter Notebook Server.
        self.server_url: str = ""

    def __enter__(self):
        """
        Initialize a JupyterServerRunner instance.

        Args:
            server_ip (str): IP address to start the server at.
            server_token (str): token to connect to the server with for user authentication.
        """
        command = (
            f"jupyter notebook --allow-root --no-browser --ip={self.server_ip} "
            f"--ServerApp.disable_check_xsrf=True --NotebookApp.token='{self.server_token}'"
        )

        # Start the Jupyter Server process and get its URL.
        self.server_process = subprocess.Popen(command.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        create_session_data = {
            "kernel": {"name": kernel_name},
            "name": notebook_path.name,
            "type": "notebook",
            "path": str(notebook_path),
        }

        with requests.Session() as session:
            session.mount("http://", JupyterServerRunner.ADAPTER)
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
