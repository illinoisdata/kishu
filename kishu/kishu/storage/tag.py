from __future__ import annotations

import sqlite3

from dataclasses import dataclass
from typing import List

from kishu.storage.checkpoint_io import TAG_TABLE
from kishu.storage.path import KishuPath


@dataclass
class TagRow:
    tag_name: str
    commit_id: str
    message: str


class KishuTag:

    @staticmethod
    def upsert_tag(notebook_id: str, tag: TagRow) -> None:
        dbfile = KishuPath.checkpoint_path(notebook_id)
        con = sqlite3.connect(dbfile)
        cur = con.cursor()
        query = f"insert or replace into {TAG_TABLE} values (?, ?, ?)"
        cur.execute(query, (tag.tag_name, tag.commit_id, tag.message))
        con.commit()

    @staticmethod
    def list_tag(notebook_id: str) -> List[TagRow]:
        dbfile = KishuPath.checkpoint_path(notebook_id)
        con = sqlite3.connect(dbfile)
        cur = con.cursor()
        query = f"select tag_name, commit_id, message from {TAG_TABLE}"
        try:
            cur.execute(query)
        except sqlite3.OperationalError:
            # No such table means no tag
            return []
        return [
            TagRow(tag_name=tag_name, commit_id=commit_id, message=message)
            for tag_name, commit_id, message in cur
        ]

    @staticmethod
    def tags_for_commit(notebook_id: str, commit_id: str) -> List[TagRow]:
        dbfile = KishuPath.checkpoint_path(notebook_id)
        con = sqlite3.connect(dbfile)
        cur = con.cursor()
        query = f"select tag_name, commit_id, message from {TAG_TABLE} where commit_id = ?"
        try:
            cur.execute(query, (commit_id,))
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        return [
            TagRow(tag_name=tag_name, commit_id=commit_id, message=message)
            for tag_name, commit_id, message in cur
        ]
