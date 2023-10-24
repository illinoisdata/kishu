import threading
import subprocess
from kishu.jupyterint import JupyterConnection
from websocket import create_connection, WebSocketTimeoutException
import requests
import urllib.request, urllib.parse
import json
import copy
import uuid
import datetime

def send_execute_request(code):
    msg_type = 'execute_request';
    content = { 'code' : code, 'silent':False }
    hdr = { 'msg_id' : uuid.uuid1().hex,
        'username': 'test',
        'session': uuid.uuid1().hex,
        'data': datetime.datetime.now().isoformat(),
        'msg_type': msg_type,
        'version' : '5.0' }
    msg = { 'header': hdr, 'parent_header': hdr,
        'metadata': {},
        'content': content }
    return msg


def test_e2e():
    #command = "jupyter notebook --no-browser --ip=127.0.0.1 --port=10000"
    command = "jupyter notebook --allow-root --no-browser --ip=127.0.0.1 --port=10000 --ServerApp.disable_check_xsrf=True --NotebookApp.password_required=False --NotebookApp.token='abcdefg'"

    # Start Jupyter Notebook
    process = subprocess.Popen(command.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(process.pid)

    # Capture the output of Jupyter Notebook and print it to the console
    try:
        output = process.stderr.readline()
        while "http:" not in output.decode() and output.decode() != '':
            output = process.stderr.readline()
        base = output.decode().split('] ')[1].split('\n')[0].split("/tree")[0]
        token = "abcdefg"
        print("base:", base)
        print("token:", token)

        # Build request header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/46.0.2490.80',
            'Authorization': 'Token ' + token
        }

        # Validate server version
        url = base + '/api/'
        response = requests.get(url, headers=headers)
        response_json = json.loads(response.text)
        print("server version:", response_json)
        assert "version" in response_json

        # Validate test notebook exists
        url = base + '/api/contents/notebooks/test_e2e.ipynb'
        response = requests.get(url, headers=headers)
        response_json = json.loads(response.text)
        assert response_json['name'] == 'test_e2e.ipynb'

        # Extract code from notebook
        code = [c['source'] for c in response_json['content']['cells']]
        print("test notebook code:")
        for c in code:
            print("-----------------------")
            print(c)

        # Create a sesson
        url = base + "/api/sessions"
        print(type(headers))
        create_session_headers = copy.deepcopy(headers)
        print(type(create_session_headers))
        create_session_data = {}
        create_session_data["kernel"] = {"name": "python3"}
        create_session_data["name"] = "test_e2e.ipynb"
        create_session_data["path"] = "notebooks/test_e2e.ipynb"
        create_session_data["type"] = "notebook"
        response = requests.post(url, headers=headers, data=json.dumps(create_session_data))
        response_json = json.loads(response.text)
        print("create session:", response_json)

        # Extract kernel id
        kernel_id = response_json["kernel"]["id"]
        print("kernel id:", kernel_id)

        # Assert the kernel has been started successfully
        url = base + "/api/kernels/" + kernel_id
        response = requests.get(url, headers=headers)
        response_json = json.loads(response.text)
        assert response_json["id"] == kernel_id
        
        # Execution request/reply is done on websockets channels
        kernel_url = base.replace("http", "ws") + "/api/kernels/" + kernel_id + "/channels"
        kernel_conn = create_connection(kernel_url, header=headers)

        # Run first kishu init cell
        kernel_conn.send(json.dumps(send_execute_request(code[0])))

        # Kishu should be able to see this new session; get its notebook key.
        result = subprocess.run(["kishu", "list"], capture_output = True, text = True)
        session_info = json.loads(result.stdout)
        notebook_key = ""
        for session in session_info["sessions"]:
            if session["kernel_id"] == kernel_id:
                notebook_key = session["notebook_key"]
                break
        assert notebook_key != ""
        print("notebook key:", notebook_key)

        # Run some cells
        for i in range(1, len(code) - 1):
            kernel_conn.send(json.dumps(send_execute_request(code[i])))

        # Get commit id of commit which we want to restore
        result = subprocess.run(["kishu", "log", notebook_key], capture_output = True, text = True)
        log_info = json.loads(result.stdout)
        commit_id = ""
        for log in log_info["commit_graph"]:
            if "indices = 123" in log["code_block"]:
                commit_id = log["commit_id"]
                break
        assert commit_id != ""
        print("commit id:", commit_id)

        # Restore to that commit
        result = subprocess.run(["kishu", "checkout", notebook_key, commit_id], capture_output = True, text = True)
        log_info = json.loads(result.stdout)
        print(log_info)

        # Run the last cell.
        kernel_conn.send(json.dumps(send_execute_request(code[-1])))

        cell_outputs = {}
        try:
            for i in range(0, len(code)):
                msg_type = ''
                while msg_type != "execute_input":
                    rsp = json.loads(kernel_conn.recv())
                    msg_type = rsp["msg_type"]
                msg_type = ''
                while msg_type != "status":
                    rsp = json.loads(kernel_conn.recv())
                    msg_type = rsp["msg_type"]
                    if msg_type == "stream":
                        cell_outputs[i] = rsp["content"]["text"]
        except WebSocketTimeoutException as _e:
            print("No output")

        # The value of the numpy array should have been restored.
        assert cell_outputs[5] == cell_outputs[8]
        print("value before checkout:", cell_outputs[5])
        print("value after checkout:", cell_outputs[8])

    except Exception as e:
        print(type(e))
        print(e)
        process.kill()
    process.kill()

test_e2e()
