import json

from flask import Flask, request
from typing import Optional

from kishu.commands import KishuCommand, into_json


def is_true(s: str) -> bool:
    return s.lower() == "true"


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


@app.get("/checkout/<notebook_id>/<branch_or_commit_id>")
def checkout(notebook_id: str, branch_or_commit_id: str):
    checkout_result = KishuCommand.checkout(notebook_id, branch_or_commit_id)
    return into_json(checkout_result)


@app.get("/branch/<notebook_id>/<branch_name>")
def branch(notebook_id: str, branch_name: str):
    commit_id: Optional[str] = request.args.get('commit_id', default=None, type=str)
    do_commit: bool = request.args.get('do_commit', default=False, type=is_true)
    branch_result = KishuCommand.branch(notebook_id, branch_name, commit_id, do_commit=do_commit)
    return into_json(branch_result)


@app.get("/tag/<notebook_id>/<tag_name>")
def tag(notebook_id: str, tag_name: str):
    commit_id: Optional[str] = request.args.get('commit_id', default=None, type=str)
    message: str = request.args.get('message', default="", type=str)
    tag_result = KishuCommand.tag(notebook_id, tag_name, commit_id, message)
    return into_json(tag_result)


@app.get("/fe/commit_graph/<notebook_id>")
def fe_commit_graph(notebook_id: str):
    fe_commit_graph_result = KishuCommand.fe_commit_graph(notebook_id)
    return into_json(fe_commit_graph_result)


@app.get("/fe/commit/<notebook_id>/<commit_id>")
def fe_commit(notebook_id: str, commit_id: str):
    vardepth = request.args.get('vardepth', default=1, type=int)
    fe_commit_result = KishuCommand.fe_commit(notebook_id, commit_id, vardepth)
    return into_json(fe_commit_result)
