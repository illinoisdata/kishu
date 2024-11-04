from __future__ import annotations

import asyncio
import multiprocessing
from pathlib import Path

import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from kishu.commands import KishuCommand, into_json
from kishu.jupyter.runtime import JupyterRuntimeEnv


def subp_kishu_init(notebook_path: str, cookies: dict, queue: multiprocessing.Queue):
    with JupyterRuntimeEnv.context(cookies=cookies):
        init_result = KishuCommand.init(Path(notebook_path))
    queue.put(into_json(init_result))


def subp_kishu_checkout(notebook_path: str, commit_id: str, cookies: dict, queue: multiprocessing.Queue):
    with JupyterRuntimeEnv.context(cookies=cookies):
        checkout_result = KishuCommand.checkout(Path(notebook_path), commit_id)
    queue.put(into_json(checkout_result))


def subp_kishu_undo(notebook_path: str, cookies: dict, queue: multiprocessing.Queue):
    with JupyterRuntimeEnv.context(cookies=cookies):
        rollback_result = KishuCommand.undo(Path(notebook_path))
    queue.put(into_json(rollback_result))


def subp_kishu_commit(notebook_path: str, message: str, cookies: dict, queue: multiprocessing.Queue):
    with JupyterRuntimeEnv.context(cookies=cookies):
        commit_result = KishuCommand.commit(Path(notebook_path), message)
    queue.put(into_json(commit_result))


class InitHandler(APIHandler):
    @tornado.gen.coroutine
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        cookies = {morsel.key: morsel.value for _, morsel in self.cookies.items()}

        # We need to run KishuCommand.init in a separate process to unblock Jupyter Server backend
        # so that our later API calls (e.g., session discovery) are unblocked.
        init_queue = multiprocessing.Queue()
        init_process = multiprocessing.Process(target=subp_kishu_init, args=(input_data["notebook_path"], cookies, init_queue))
        init_process.start()
        while init_queue.empty():
            # Awaiting to unblock.
            yield asyncio.sleep(0.5)
        init_result_json = init_queue.get()
        init_process.join()

        self.finish(init_result_json)


class LogAllHandler(APIHandler):
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        log_all_result = KishuCommand.log_all(Path(input_data["notebook_path"]))
        self.finish(into_json(log_all_result))


class CheckoutHandler(APIHandler):
    @tornado.gen.coroutine
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        cookies = {morsel.key: morsel.value for _, morsel in self.cookies.items()}

        # We need to run KishuCommand.checkout in a separate process to unblock Jupyter Server backend
        # so that the frontend reload does not cause a deadlock.
        checkout_queue = multiprocessing.Queue()
        checkout_process = multiprocessing.Process(
            target=subp_kishu_checkout, args=(input_data["notebook_path"], input_data["commit_id"], cookies, checkout_queue)
        )
        checkout_process.start()
        while checkout_queue.empty():
            # Awaiting to unblock.
            yield asyncio.sleep(0.5)
        checkout_result = checkout_queue.get()
        checkout_process.join()

        self.finish(checkout_result)


class CommitHandler(APIHandler):
    @tornado.gen.coroutine
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        cookies = {morsel.key: morsel.value for _, morsel in self.cookies.items()}

        # We need to run KishuCommand.checkout in a separate process to unblock Jupyter Server backend
        # so that the frontend reload does not cause a deadlock.
        commit_queue = multiprocessing.Queue()
        commit_process = multiprocessing.Process(
            target=subp_kishu_commit, args=(input_data["notebook_path"], input_data["message"], cookies, commit_queue)
        )
        commit_process.start()
        while commit_queue.empty():
            # Awaiting to unblock.
            yield asyncio.sleep(0.5)
        commit_result = commit_queue.get()
        commit_process.join()

        self.finish(commit_result)


class UndoHandler(APIHandler):
    @tornado.gen.coroutine
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        cookies = {morsel.key: morsel.value for _, morsel in self.cookies.items()}

        # We need to run KishuCommand.undo in a separate process to unblock Jupyter Server backend
        # so that the frontend reload does not cause a deadlock.
        undo_queue = multiprocessing.Queue()
        undo_process = multiprocessing.Process(target=subp_kishu_undo, args=(input_data["notebook_path"], cookies, undo_queue))
        undo_process.start()
        while undo_queue.empty():
            # Awaiting to unblock.
            yield asyncio.sleep(0.5)
        undo_result = undo_queue.get()
        undo_process.join()
        self.finish(undo_result)


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    kishu_url = url_path_join(base_url, "kishu")
    handlers = [
        (url_path_join(kishu_url, "init"), InitHandler),
        (url_path_join(kishu_url, "log_all"), LogAllHandler),
        (url_path_join(kishu_url, "checkout"), CheckoutHandler),
        (url_path_join(kishu_url, "commit"), CommitHandler),
        (url_path_join(kishu_url, "undo"), UndoHandler),
    ]
    web_app.add_handlers(host_pattern, handlers)
