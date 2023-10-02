from __future__ import annotations
import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

from kishu.commands import KishuCommand
from kishu.serialization import into_json


class LogAllHandler(APIHandler):
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        log_all_result = KishuCommand.log_all(input_data["notebook_id"])
        self.finish(into_json(log_all_result))


class CheckoutHandler(APIHandler):
    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        checkout_result = KishuCommand.checkout(input_data["notebook_id"], input_data["commit_id"])
        self.finish(into_json(checkout_result))


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    kishu_url = url_path_join(base_url, "kishu")
    handlers = [
        (url_path_join(kishu_url, "log_all"), LogAllHandler),
        (url_path_join(kishu_url, "checkout"), CheckoutHandler),
    ]
    web_app.add_handlers(host_pattern, handlers)
