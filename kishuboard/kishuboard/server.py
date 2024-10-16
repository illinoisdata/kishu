import json
import os
from pathlib import Path
from typing import Any, Callable, Optional

from flask import Flask, Request, jsonify, request, send_from_directory
from flask_cors import CORS
from kishu.commands import KishuCommand, into_json

# Determine the directory of the current file (app.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the static directory
static_dir = os.path.join(current_dir, "build")

app = Flask("kishu_server", static_folder=static_dir)
CORS(app)


"""
Exceptions and handling.
"""


class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = InvalidAPIUsage.status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidAPIUsage)
def invalid_api_usage(e):
    return jsonify(e.to_dict()), e.status_code


"""
Argument parsers.
"""


def is_true(s: str) -> bool:
    return s.lower() == "true"


def get_required_arg(key: str, type_fn: Callable[[str], Any]) -> Any:
    value_str: Optional[str] = request.args.get(key, default=None)
    if value_str is None:
        raise InvalidAPIUsage(f"Missing required argument {key}.")
    try:
        return type_fn(value_str)
    except Exception as e:
        raise InvalidAPIUsage(f"Failed parsing required argument {key} with error {repr(e)}")


def get_optional_arg(key: str, default: Any, type_fn: Callable[[str], Any]) -> Any:
    value_str: Optional[str] = request.args.get(key, default=None)
    if value_str is None:
        return default
    try:
        return type_fn(value_str)
    except Exception as e:
        raise InvalidAPIUsage(f"Failed parsing required argument {key} with error {repr(e)}")


"""
Endpoints.
"""


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
    list_all: bool = get_optional_arg("list_all", default=False, type_fn=is_true)
    list_result = KishuCommand.list(list_all=list_all)
    return into_json(list_result)


@app.get("/api/log")
def log() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    commit_id: Optional[str] = get_optional_arg("commit_id", default=None, type_fn=str)
    log_result = KishuCommand.log(notebook_path, commit_id)
    return into_json(log_result)


@app.get("/api/log_all")
def log_all() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    log_all_result = KishuCommand.log_all(notebook_path)
    return into_json(log_all_result)


@app.get("/api/status")
def status() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    commit_id: str = get_required_arg("commit_id", type_fn=str)
    status_result = KishuCommand.status(notebook_path, commit_id)
    return into_json(status_result)


@app.get("/api/checkout")
def checkout() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    branch_or_commit_id: str = get_required_arg("branch_or_commit_id", type_fn=str)
    skip_notebook: bool = get_optional_arg("skip_notebook", default=False, type_fn=is_true)
    checkout_result = KishuCommand.checkout(
        notebook_path,
        branch_or_commit_id,
        skip_notebook=skip_notebook,
    )
    return into_json(checkout_result)


@app.get("/api/branch")
def branch() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    branch_name: str = get_required_arg("branch_name", type_fn=str)
    commit_id: Optional[str] = get_optional_arg("commit_id", default=None, type_fn=str)
    do_commit: bool = get_optional_arg("do_commit", default=False, type_fn=is_true)
    branch_result = KishuCommand.branch(notebook_path, branch_name, commit_id, do_commit=do_commit)
    return into_json(branch_result)


@app.get("/api/delete_branch")
def delete_branch() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    branch_name: str = get_required_arg("branch_name", type_fn=str)
    delete_branch_result = KishuCommand.delete_branch(notebook_path, branch_name)
    return into_json(delete_branch_result)


@app.get("/api/rename_branch")
def rename_branch() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    old_branch_name: str = get_required_arg("old_branch_name", type_fn=str)
    new_branch_name: str = get_required_arg("new_branch_name", type_fn=str)
    rename_branch_result = KishuCommand.rename_branch(notebook_path, old_branch_name, new_branch_name)
    return into_json(rename_branch_result)


@app.get("/api/tag")
def tag() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    tag_name: str = get_required_arg("tag_name", type_fn=str)
    commit_id: Optional[str] = get_optional_arg("commit_id", default=None, type_fn=str)
    message: str = get_optional_arg("message", default="", type_fn=str)
    tag_result = KishuCommand.tag(notebook_path, tag_name, commit_id, message)
    return into_json(tag_result)


# APIs that can only be used by the frontend to get information
@app.get("/api/delete_tag")
def delete_tag() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    tag_name: str = get_required_arg("tag_name", type_fn=str)
    delete_tag_result = KishuCommand.delete_tag(notebook_path, tag_name)
    return into_json(delete_tag_result)


@app.get("/api/fe/commit_graph")
def fe_commit_graph() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    fe_commit_graph_result = KishuCommand.fe_commit_graph(notebook_path)
    return into_json(fe_commit_graph_result)


@app.get("/api/fe/commit")
def fe_commit() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    commit_id: str = get_required_arg("commit_id", type_fn=str)
    vardepth = get_optional_arg("vardepth", default=1, type_fn=int)
    fe_commit_result = KishuCommand.fe_commit(notebook_path, commit_id, vardepth)
    return into_json(fe_commit_result)


@app.get("/api/fe/code_diff")
def fe_code_diff() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    from_commit_id: str = get_required_arg("from_commit_id", type_fn=str)
    to_commit_id: str = get_required_arg("to_commit_id", type_fn=str)
    fe_code_diff_result = KishuCommand.fe_code_diff(notebook_path, from_commit_id, to_commit_id)
    return into_json(fe_code_diff_result)


@app.get("/api/fe/find_var_change")
def fe_find_var_change() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    variable_name: str = get_required_arg("variable_name", type_fn=str)
    fe_commit_filter_result = KishuCommand.find_var_change(notebook_path, variable_name)
    return into_json(fe_commit_filter_result)


@app.get("/api/fe/var_diff")
def fe_var_diff() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    from_commit_id: str = get_required_arg("from_commit_id", type_fn=str)
    to_commit_id: str = get_required_arg("to_commit_id", type_fn=str)
    fe_var_diff_result = KishuCommand.fe_variable_diff(notebook_path, from_commit_id, to_commit_id)
    return into_json(fe_var_diff_result)


@app.get("/api/fe/edit_message")
def fe_edit_message() -> str:
    notebook_path: Path = get_required_arg("notebook_path", type_fn=Path)
    commit_id: str = get_required_arg("commit_id", type_fn=str)
    new_message: str = get_required_arg("new_message", type_fn=str)
    fe_edit_message_result = KishuCommand.edit_commit(notebook_path, commit_id, new_message)
    return into_json(fe_edit_message_result)


def main() -> None:
    app.run(port=4999)


if __name__ == "__main__":
    main()
