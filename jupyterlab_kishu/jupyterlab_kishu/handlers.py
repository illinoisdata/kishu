from __future__ import annotations
import asyncio
import multiprocessing
import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

from kishu.commands import KishuCommand, into_json
from kishu.runtime import JupyterRuntimeEnv
from kishu.notebook_id import NotebookId


def subp_kishu_init(notebook_path, queue, cookies):
    with JupyterRuntimeEnv.context(cookies=cookies):
        init_result = KishuCommand.init(notebook_path)
    queue.put(into_json(init_result))


class InitHandler(APIHandler):
    @tornado.gen.coroutine
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        cookies = {morsel.key: morsel.value for _, morsel in self.cookies.items()}

        # We need to run KishuCommand.init in a separate process to unblock Jupyter Server backend
        # so that our later API calls (e.g., session discovery) are unblocked.
        init_queue = multiprocessing.Queue()
        init_process = multiprocessing.Process(
            target=subp_kishu_init,
            args=(input_data["notebook_path"], init_queue, cookies)
        )
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
        notebook_key = NotebookId.parse_key_from_path_or_key(input_data["notebook_path"])
        log_all_result = KishuCommand.log_all(notebook_key)
        self.finish(into_json(log_all_result))


class CheckoutHandler(APIHandler):
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        notebook_key = NotebookId.parse_key_from_path_or_key(input_data["notebook_path"])
        checkout_result = KishuCommand.checkout(notebook_key, input_data["commit_id"])
        self.finish(into_json(checkout_result))


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    kishu_url = url_path_join(base_url, "kishu")
    handlers = [
        (url_path_join(kishu_url, "init"), InitHandler),
        (url_path_join(kishu_url, "log_all"), LogAllHandler),
        (url_path_join(kishu_url, "checkout"), CheckoutHandler),
    ]
    web_app.add_handlers(host_pattern, handlers)
