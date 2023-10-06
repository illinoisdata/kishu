from __future__ import annotations

import json
import sqlite3

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List, Optional

from kishu.storage.checkpoint_io import BRANCH_TABLE
from kishu.storage.path import KishuPath


@dataclass_json
@dataclass
class HeadBranch:
    branch_name: Optional[str]
    commit_id: Optional[str]


@dataclass
class BranchRow:
    branch_name: str
    commit_id: str


class KishuBranch:

    @staticmethod
    def get_head(notebook_id: str) -> HeadBranch:
        try:
            with open(KishuPath.head_path(notebook_id), "r") as f:
                json_str = f.read()
                return HeadBranch.from_json(json_str)  # type: ignore
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return HeadBranch(branch_name=None, commit_id=None)

    @staticmethod
    def update_head(
        notebook_id: str,
        branch_name: Optional[str] = None,
        commit_id: Optional[str] = None,
        is_detach: bool = False
    ) -> HeadBranch:
        head = KishuBranch.get_head(notebook_id)
        if head is None:
            head = HeadBranch(branch_name=None, commit_id=None)
        if branch_name is not None or is_detach:
            head.branch_name = branch_name
        if commit_id is not None:
            head.commit_id = commit_id
        with open(KishuPath.head_path(notebook_id), 'w') as f:
            f.write(head.to_json())  # type: ignore
        return head

    @staticmethod
    def upsert_branch(notebook_id: str, branch: str, commit_id: str) -> None:
        dbfile = KishuPath.checkpoint_path(notebook_id)
        con = sqlite3.connect(dbfile)
        cur = con.cursor()
        query = f"insert or replace into {BRANCH_TABLE} values (?, ?)"
        cur.execute(query, (branch, commit_id))
        con.commit()

    @staticmethod
    def list_branch(notebook_id: str) -> List[BranchRow]:
        dbfile = KishuPath.checkpoint_path(notebook_id)
        con = sqlite3.connect(dbfile)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE}"
        try:
            cur.execute(query)
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        return [
            BranchRow(branch_name=branch_name, commit_id=commit_id)
            for branch_name, commit_id in cur
        ]

    @staticmethod
    def get_branch(notebook_id: str, branch_name: str) -> List[BranchRow]:
        dbfile = KishuPath.checkpoint_path(notebook_id)
        con = sqlite3.connect(dbfile)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE} where branch_name = ?"
        try:
            cur.execute(query, (branch_name,))
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        return [
            BranchRow(branch_name=branch_name, commit_id=commit_id)
            for branch_name, commit_id in cur
        ]

    @staticmethod
    def rename_branch(notebook_id: str, old_name: str, new_name: str) -> None:
        dbfile = KishuPath.checkpoint_path(notebook_id)
        con = sqlite3.connect(dbfile)
        cur = con.cursor()

        if not KishuBranch.contains_branch(cur, old_name):
            raise ValueError("The provided old branch name does not exist.")
        if KishuBranch.contains_branch(cur, new_name):
            raise ValueError("The provided new branch name already exists.")

        query = f"update {BRANCH_TABLE} set branch_name = ? where branch_name = ?"
        cur.execute(query, (new_name, old_name))
        con.commit()

        # Update HEAD branch if HEAD is on branch
        head = KishuBranch.get_head(notebook_id)
        if old_name == head.branch_name:
            KishuBranch.update_head(notebook_id, branch_name=new_name)

    @staticmethod
    def contains_branch(cur: sqlite3.Cursor, branch_name: str) -> bool:
        query = f"select count(*) from {BRANCH_TABLE} where branch_name = ?"
        cur.execute(query, (branch_name,))
        return cur.fetchone()[0] == 1
