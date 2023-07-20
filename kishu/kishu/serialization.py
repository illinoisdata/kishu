from __future__ import annotations
import dataclasses
import json


"""
Printing dataclasses
"""


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
