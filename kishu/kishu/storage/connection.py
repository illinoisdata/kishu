from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kishu.storage.path import KishuPath

CONNECTION_TABLE = "connection"
CONNECTION_KEY = "CONN"


@dataclass
class JupyterConnectionInfo:
    kernel_id: str
    notebook_path: str


"""
Kishu Jupyter connection information.
"""


class KishuConnection:

    def __init__(self, key: str, path: Path, kernel_id: str):
        self._key = key
        self._path = path
        self._kernel_id = kernel_id
        self.database_path = KishuPath.database_path(self._key)

    def init_database(self) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"create table if not exists {CONNECTION_TABLE} (conn primary key, kernel_id text, notebook_path text)")
        con.commit()

    def drop_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"drop table if exists {CONNECTION_TABLE}")
        con.commit()

    def record_connection(self) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"insert or replace into {CONNECTION_TABLE} values ('{CONNECTION_KEY}', ?, ?)"
        cur.execute(query, (self._kernel_id, str(self._path)))
        con.commit()

    @staticmethod
    def try_retrieve_connection(key: str) -> Optional[JupyterConnectionInfo]:
        con = sqlite3.connect(KishuPath.database_path(key))
        cur = con.cursor()
        try:
            cur.execute(f"select kernel_id, notebook_path from {CONNECTION_TABLE} where conn = '{CONNECTION_KEY}'")
            res: Optional[tuple] = cur.fetchone()
            if not res:
                return None
            kernel_id, notebook_path = res
            return JupyterConnectionInfo(kernel_id=kernel_id, notebook_path=notebook_path)
        except sqlite3.OperationalError:
            return None
        finally:
            con.close()
