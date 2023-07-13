from flask import Flask

import json

from kishu.serialization import into_json
from kishu.commands import KishuCommand


app = Flask("kishu_server")


@app.get("/health")
def health():
    return json.dumps({"status": "ok"})


@app.get("/log/<notebook_id>/<commit_id>")
def log(notebook_id: str, commit_id: str):
    log_result = KishuCommand.log(notebook_id, commit_id)
    return into_json(log_result)


@app.get("/log_all/<notebook_id>")
def log_all(notebook_id: str):
    log_all_result = KishuCommand.log_all(notebook_id)
    return into_json(log_all_result)


@app.get("/status/<notebook_id>/<commit_id>")
def status(notebook_id: str, commit_id: str):
    status_result = KishuCommand.status(notebook_id, commit_id)
    return into_json(status_result)


@app.get("/fe/initialize/<notebook_id>")
def fe_initialize(notebook_id: str):
    fe_initialize_result = KishuCommand.fe_initialize(notebook_id)
    return into_json(fe_initialize_result)


@app.get("/fe/history/<notebook_id>/<commit_id>")
def fe_history(notebook_id: str, commit_id: str):
    fe_history_result = KishuCommand.fe_history(notebook_id, commit_id)
    return into_json(fe_history_result)
