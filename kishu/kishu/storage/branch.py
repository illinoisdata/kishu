from __future__ import annotations

import json
import sqlite3

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, List, Optional

from kishu.exceptions import (
    BranchNotFoundError,
    BranchConflictError,
)
from kishu.storage.path import KishuPath


BRANCH_TABLE = 'branch'


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

    def __init__(self, notebook_id: str):
        self.database_path = KishuPath.database_path(notebook_id)
        self.head_path = KishuPath.head_path(notebook_id)

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f'create table if not exists {BRANCH_TABLE} (branch_name text primary key, commit_id text)')
        con.commit()

    def get_head(self) -> HeadBranch:
        try:
            with open(self.head_path, "r") as f:
                json_str = f.read()
                return HeadBranch.from_json(json_str)  # type: ignore
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return HeadBranch(branch_name=None, commit_id=None)

    def update_head(
        self,
        branch_name: Optional[str] = None,
        commit_id: Optional[str] = None,
        is_detach: bool = False
    ) -> HeadBranch:
        # Get current head.
        head = self.get_head()
        if head is None:
            head = HeadBranch(branch_name=None, commit_id=None)

        # Assign head branch.
        if is_detach:
            head.branch_name = None
        elif branch_name is not None:
            head.branch_name = branch_name

        # Assign commit ID.
        if commit_id is not None:
            head.commit_id = commit_id

        # Write head.
        with open(self.head_path, 'w') as f:
            f.write(head.to_json())  # type: ignore
        return head

    def upsert_branch(self, branch: str, commit_id: str) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"insert or replace into {BRANCH_TABLE} values (?, ?)"
        cur.execute(query, (branch, commit_id))
        con.commit()

    def list_branch(self) -> List[BranchRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE}"
        try:
            cur.execute(query)
            return [
                BranchRow(branch_name=branch_name, commit_id=commit_id)
                for branch_name, commit_id in cur
            ]
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        finally:
            con.close()

    def get_branch(self, branch_name: str) -> List[BranchRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE} where branch_name = ?"
        try:
            cur.execute(query, (branch_name,))
            return [
                BranchRow(branch_name=branch_name, commit_id=commit_id)
                for branch_name, commit_id in cur
            ]
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        finally:
            con.close()

    def branches_for_commit(self, commit_id: str) -> List[BranchRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE} where commit_id = ?"
        try:
            cur.execute(query, (commit_id,))
            return [
                BranchRow(branch_name=branch_name, commit_id=commit_id)
                for branch_name, commit_id in cur
            ]
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        finally:
            con.close()

    def branches_for_many_commits(self, commit_ids: List[str],) -> Dict[str, List[BranchRow]]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = "select branch_name, commit_id from {} where commit_id in ({})".format(
            BRANCH_TABLE,
            ', '.join('?' * len(commit_ids))
        )
        try:
            cur.execute(query, commit_ids)
        except sqlite3.OperationalError:
            # No such table means no branch
            return {}
        raw_branches = cur.fetchall()
        branch_by_commit: Dict[str, List[BranchRow]] = {}
        for branch_name, commit_id in raw_branches:
            if commit_id not in branch_by_commit:
                branch_by_commit[commit_id] = []
            branch_by_commit[commit_id].append(BranchRow(
                branch_name=branch_name,
                commit_id=commit_id,
            ))
        con.close()
        return branch_by_commit

    def delete_branch(self, branch_name: str) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        head = self.get_head()
        if branch_name == head.branch_name:
            raise BranchConflictError("Cannot delete the currently checked-out branch.")
        if not KishuBranch.contains_branch(cur, branch_name):
            raise BranchNotFoundError(branch_name)

        query = f"delete from {BRANCH_TABLE} where branch_name = ?"
        cur.execute(query, (branch_name,))
        con.commit()

    def rename_branch(self, old_name: str, new_name: str) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        if not KishuBranch.contains_branch(cur, old_name):
            raise BranchNotFoundError(old_name)
        if KishuBranch.contains_branch(cur, new_name):
            raise BranchConflictError("The provided new branch name already exists.")

        query = f"update {BRANCH_TABLE} set branch_name = ? where branch_name = ?"
        cur.execute(query, (new_name, old_name))
        con.commit()

        # Update HEAD branch if HEAD is on branch
        head = self.get_head()
        if old_name == head.branch_name:
            self.update_head(branch_name=new_name)

    @staticmethod
    def contains_branch(cur: sqlite3.Cursor, branch_name: str) -> bool:
        query = f"select count(*) from {BRANCH_TABLE} where branch_name = ?"
        cur.execute(query, (branch_name,))
        return cur.fetchone()[0] == 1
