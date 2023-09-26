from __future__ import annotations
import dataclasses
import json
import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

from kishu.commands import KishuCommand


class DataclassJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        try:
            return super().default(o)
        except TypeError:
            return o.__repr__()


def into_json(data):
    return json.dumps(data, cls=DataclassJSONEncoder, indent=2)


class CheckoutHandler(APIHandler):
    @tornado.web.authenticated
    def post(self):
        # input_data is a dictionary with a key "name"
        input_data = self.get_json_body()
        checkout_result = KishuCommand.checkout(input_data["notebook_id"], input_data["commit_id"])
        self.finish(into_json(checkout_result))


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    kishu_url = url_path_join(base_url, "kishu")

    """
    Checkout
    """

    route_pattern = url_path_join(kishu_url, "checkout")
    handlers = [(route_pattern, CheckoutHandler)]
    web_app.add_handlers(host_pattern, handlers)
