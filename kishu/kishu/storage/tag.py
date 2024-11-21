from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from kishu.exceptions import TagNotFoundError

TAG_TABLE = "tag"


TAG_TABLE_COMMIT_ID_IDX = "tag_commit_id_idx"


@dataclass
class TagRow:
    tag_name: str
    commit_id: str
    message: str


class KishuTag:

    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"create table if not exists {TAG_TABLE} (tag_name text primary key, commit_id text, message text)")
        cur.execute(f"create index if not exists {TAG_TABLE_COMMIT_ID_IDX} on {TAG_TABLE} (commit_id)")
        con.commit()

    def upsert_tag(self, tag: TagRow) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"insert or replace into {TAG_TABLE} values (?, ?, ?)"
        cur.execute(query, (tag.tag_name, tag.commit_id, tag.message))
        con.commit()

    def list_tag(self) -> List[TagRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select tag_name, commit_id, message from {TAG_TABLE}"
        try:
            cur.execute(query)
            return [TagRow(tag_name=tag_name, commit_id=commit_id, message=message) for tag_name, commit_id, message in cur]
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
            return [TagRow(tag_name=tag_name, commit_id=commit_id, message=message) for tag_name, commit_id, message in cur]
        except sqlite3.OperationalError:
            # No such table means no tag
            return []
        finally:
            con.close()

    def tags_for_many_commits(self, commit_ids: List[str]) -> Dict[str, List[TagRow]]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = "select tag_name, commit_id, message from {} where commit_id in ({})".format(
            TAG_TABLE, ", ".join("?" * len(commit_ids))
        )
        try:
            cur.execute(query, commit_ids)
            raw_tags = cur.fetchall()
            tag_by_commit: Dict[str, List[TagRow]] = {}
            for tag_name, commit_id, message in raw_tags:
                if commit_id not in tag_by_commit:
                    tag_by_commit[commit_id] = []
                tag_by_commit[commit_id].append(
                    TagRow(
                        tag_name=tag_name,
                        commit_id=commit_id,
                        message=message,
                    )
                )
            return tag_by_commit
        except sqlite3.OperationalError:
            # No such table means no tag
            return {}
        finally:
            con.close()

    def delete_tag(self, tag_name: str) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        if not KishuTag._contains_tag(cur, tag_name):
            raise TagNotFoundError(tag_name)

        query = f"delete from {TAG_TABLE} where tag_name = ?"
        cur.execute(query, (tag_name,))
        con.commit()

    @staticmethod
    def _contains_tag(cur: sqlite3.Cursor, tag_name: str) -> bool:
        query = f"select count(*) from {TAG_TABLE} where tag_name = ?"
        cur.execute(query, (tag_name,))
        return cur.fetchone()[0] == 1
