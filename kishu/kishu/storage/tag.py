from __future__ import annotations

import sqlite3

from dataclasses import dataclass
from typing import Dict, List

from kishu.storage.path import KishuPath


TAG_TABLE = 'tag'


@dataclass
class TagRow:
    tag_name: str
    commit_id: str
    message: str


class KishuTag:

    def __init__(self, notebook_id: str):
        self.database_path = KishuPath.database_path(notebook_id)

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f'create table if not exists {TAG_TABLE} (tag_name text primary key, commit_id text, message text)')
        con.commit()

    def upsert_tag(self, tag: TagRow) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"insert or replace into {TAG_TABLE} values (?, ?, ?)"
        cur.execute(query, (tag.tag_name, tag.commit_id, tag.message))
        con.commit()

    def list_tag(self, ) -> List[TagRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select tag_name, commit_id, message from {TAG_TABLE}"
        try:
            cur.execute(query)
            return [
                TagRow(tag_name=tag_name, commit_id=commit_id, message=message)
                for tag_name, commit_id, message in cur
            ]
        except sqlite3.OperationalError:
            # No such table means no tag
            return []
        finally:
            con.close()

    def tags_for_commit(self, commit_id: str) -> List[TagRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select tag_name, commit_id, message from {TAG_TABLE} where commit_id = ?"
        try:
            cur.execute(query, (commit_id,))
            return [
                TagRow(tag_name=tag_name, commit_id=commit_id, message=message)
                for tag_name, commit_id, message in cur
            ]
        except sqlite3.OperationalError:
            # No such table means no tag
            return []
        finally:
            con.close()

    def tags_for_many_commits(self, commit_ids: List[str]) -> Dict[str, List[TagRow]]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = "select tag_name, commit_id, message from {} where commit_id in ({})".format(
            TAG_TABLE,
            ', '.join('?' * len(commit_ids))
        )
        try:
            cur.execute(query, commit_ids)
            raw_tags = cur.fetchall()
            tag_by_commit: Dict[str, List[TagRow]] = {}
            for tag_name, commit_id, message in raw_tags:
                if commit_id not in tag_by_commit:
                    tag_by_commit[commit_id] = []
                tag_by_commit[commit_id].append(TagRow(
                    tag_name=tag_name,
                    commit_id=commit_id,
                    message=message,
                ))
            return tag_by_commit
        except sqlite3.OperationalError:
            # No such table means no tag
            return {}
        finally:
            con.close()
