import json

from flask import Flask, request
from flask_cors import CORS
from typing import Optional

from kishu.commands import KishuCommand, into_json


def is_true(s: str) -> bool:
    return s.lower() == "true"


app = Flask("kishu_server")
CORS(app)


@app.get("/health")
def health():
    return json.dumps({"status": "ok"})


@app.get("/list")
def list() -> str:
    list_all: bool = request.args.get('list_all', default=False, type=is_true)
    list_result = KishuCommand.list(list_all=list_all)
    return into_json(list_result)


@app.get("/log/<notebook_id>")
def log(notebook_id: str) -> str:
    commit_id: Optional[str] = request.args.get('commit_id', default=None, type=str)
    log_result = KishuCommand.log(notebook_id, commit_id)
    return into_json(log_result)


@app.get("/log_all/<notebook_id>")
def log_all(notebook_id: str) -> str:
    log_all_result = KishuCommand.log_all(notebook_id)
    return into_json(log_all_result)


@app.get("/status/<notebook_id>/<commit_id>")
def status(notebook_id: str, commit_id: str) -> str:
    status_result = KishuCommand.status(notebook_id, commit_id)
    return into_json(status_result)


@app.get("/checkout/<notebook_id>/<branch_or_commit_id>")
def checkout(notebook_id: str, branch_or_commit_id: str) -> str:
    skip_notebook: bool = request.args.get('skip_notebook', default=False, type=is_true)
    checkout_result = KishuCommand.checkout(
        notebook_id,
        branch_or_commit_id,
        skip_notebook=skip_notebook,
    )
    return into_json(checkout_result)


@app.get("/branch/<notebook_id>/<branch_name>")
def branch(notebook_id: str, branch_name: str) -> str:
    commit_id: Optional[str] = request.args.get('commit_id', default=None, type=str)
    do_commit: bool = request.args.get('do_commit', default=False, type=is_true)
    branch_result = KishuCommand.branch(notebook_id, branch_name, commit_id, do_commit=do_commit)
    return into_json(branch_result)


@app.get("/tag/<notebook_id>/<tag_name>")
def tag(notebook_id: str, tag_name: str) -> str:
    commit_id: Optional[str] = request.args.get('commit_id', default=None, type=str)
    message: str = request.args.get('message', default="", type=str)
    tag_result = KishuCommand.tag(notebook_id, tag_name, commit_id, message)
    return into_json(tag_result)


@app.get("/fe/commit_graph/<notebook_id>")
def fe_commit_graph(notebook_id: str) -> str:
    fe_commit_graph_result = KishuCommand.fe_commit_graph(notebook_id)
    return into_json(fe_commit_graph_result)


@app.get("/fe/commit/<notebook_id>/<commit_id>")
def fe_commit(notebook_id: str, commit_id: str):
    vardepth = request.args.get('vardepth', default=1, type=int)
    fe_commit_result = KishuCommand.fe_commit(notebook_id, commit_id, vardepth)
    return into_json(fe_commit_result)


@app.get("/fe/diff/<notebook_id>/<from_commit_id>/<to_commit_id>")
def fe_commit_diff(notebook_id: str, from_commit_id: str, to_commit_id: str):
    fe_commit_diff_result = KishuCommand.fe_commit_diff(notebook_id, from_commit_id, to_commit_id)
    return into_json(fe_commit_diff_result)


@app.get("/fe/commit_filter/<notebook_id>/<variable_name>")
def fe_commit_filter(notebook_id: str, variable_name: str):
    fe_commit_filter_result = KishuCommand.commit_filter(notebook_id, variable_name)
    return into_json(fe_commit_filter_result)