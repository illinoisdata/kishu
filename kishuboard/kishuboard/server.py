import json
import os
from typing import Optional

from flask import Flask, request, send_from_directory
from flask_cors import CORS
from kishu.commands import KishuCommand, into_json


def is_true(s: str) -> bool:
    return s.lower() == "true"


# Determine the directory of the current file (app.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the static directory
static_dir = os.path.join(current_dir, "build")

app = Flask("kishu_server", static_folder=static_dir)
CORS(app)


# Serve React App (frontend endpoints)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(app.static_folder + "/" + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


# Backend endpoints
@app.get("/api/health")
def health():
    return json.dumps({"status": "ok"})


@app.get("/api/list")
def list() -> str:
    list_all: bool = request.args.get("list_all", default=False, type=is_true)
    list_result = KishuCommand.list(list_all=list_all)
    return into_json(list_result)


@app.get("/api/log/<notebook_id>")
def log(notebook_id: str) -> str:
    commit_id: Optional[str] = request.args.get("commit_id", default=None, type=str)
    log_result = KishuCommand.log(notebook_id, commit_id)
    return into_json(log_result)


@app.get("/api/log_all/<notebook_id>")
def log_all(notebook_id: str) -> str:
    log_all_result = KishuCommand.log_all(notebook_id)
    return into_json(log_all_result)


@app.get("/api/status/<notebook_id>/<commit_id>")
def status(notebook_id: str, commit_id: str) -> str:
    status_result = KishuCommand.status(notebook_id, commit_id)
    return into_json(status_result)


@app.get("/api/checkout/<notebook_id>/<branch_or_commit_id>")
def checkout(notebook_id: str, branch_or_commit_id: str) -> str:
    skip_notebook: bool = request.args.get("skip_notebook", default=False, type=is_true)
    checkout_result = KishuCommand.checkout(
        notebook_id,
        branch_or_commit_id,
        skip_notebook=skip_notebook,
    )
    return into_json(checkout_result)


@app.get("/api/branch/<notebook_id>/<branch_name>")
def branch(notebook_id: str, branch_name: str) -> str:
    commit_id: Optional[str] = request.args.get("commit_id", default=None, type=str)
    do_commit: bool = request.args.get("do_commit", default=False, type=is_true)
    branch_result = KishuCommand.branch(notebook_id, branch_name, commit_id, do_commit=do_commit)
    return into_json(branch_result)


@app.get("/api/delete_branch/<notebook_id>/<branch_name>")
def delete_branch(notebook_id: str, branch_name: str) -> str:
    delete_branch_result = KishuCommand.delete_branch(notebook_id, branch_name)
    return into_json(delete_branch_result)


@app.get("/api/rename_branch/<notebook_id>/<old_branch_name>/<new_branch_name>")
def rename_branch(notebook_id: str, old_branch_name: str, new_branch_name: str) -> str:
    rename_branch_result = KishuCommand.rename_branch(notebook_id, old_branch_name, new_branch_name)
    return into_json(rename_branch_result)


@app.get("/api/tag/<notebook_id>/<tag_name>")
def tag(notebook_id: str, tag_name: str) -> str:
    commit_id: Optional[str] = request.args.get("commit_id", default=None, type=str)
    message: str = request.args.get("message", default="", type=str)
    tag_result = KishuCommand.tag(notebook_id, tag_name, commit_id, message)
    return into_json(tag_result)


# APIs that can only be used by the frontend to get information
@app.get("/api/delete_tag/<notebook_id>/<tag_name>")
def delete_tag(notebook_id: str, tag_name: str) -> str:
    delete_tag_result = KishuCommand.delete_tag(notebook_id, tag_name)
    return into_json(delete_tag_result)


@app.get("/api/fe/commit_graph/<notebook_id>")
def fe_commit_graph(notebook_id: str) -> str:
    fe_commit_graph_result = KishuCommand.fe_commit_graph(notebook_id)
    return into_json(fe_commit_graph_result)


@app.get("/api/fe/commit/<notebook_id>/<commit_id>")
def fe_commit(notebook_id: str, commit_id: str):
    vardepth = request.args.get("vardepth", default=1, type=int)
    fe_commit_result = KishuCommand.fe_commit(notebook_id, commit_id, vardepth)
    return into_json(fe_commit_result)


@app.get("/api/fe/code_diff/<notebook_id>/<from_commit_id>/<to_commit_id>")
def fe_code_diff(notebook_id: str, from_commit_id: str, to_commit_id: str):
    fe_code_diff_result = KishuCommand.fe_code_diff(notebook_id, from_commit_id, to_commit_id)
    return into_json(fe_code_diff_result)


@app.get("/api/fe/find_var_change/<notebook_id>/<variable_name>")
def fe_find_var_change(notebook_id: str, variable_name: str):
    fe_commit_filter_result = KishuCommand.find_var_change(notebook_id, variable_name)
    return into_json(fe_commit_filter_result)


@app.get("/api/fe/var_diff/<notebook_id>/<from_commit_id>/<to_commit_id>")
def fe_var_diff(notebook_id: str, from_commit_id: str, to_commit_id: str):
    fe_var_diff_result = KishuCommand.fe_variable_diff(notebook_id, from_commit_id, to_commit_id)
    return into_json(fe_var_diff_result)


@app.get("/api/fe/edit_message/<notebook_id>/<commit_id>/<new_message>")
def fe_edit_message(notebook_id: str, commit_id: str, new_message: str):
    fe_edit_message_result = KishuCommand.edit_commit(notebook_id, commit_id, new_message)
    return into_json(fe_edit_message_result)


def main() -> None:
    app.run(port=4999)


if __name__ == "__main__":
    main()
