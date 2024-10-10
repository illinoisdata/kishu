from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from kishu.storage.path import KishuPath

CommitId = str
ABSOLUTE_PAST: CommitId = ""  # Logically first commit (e.g., commit graph's root).

VARIABLE_GRAPH_NAME: str = "var"
NOTEBOOK_GRAPH_NAME: str = "nb"
COMMIT_PARENT_TABLE_SUFFIX: str = "commit_parent"
HEAD_COMMIT_TABLE_SUFFIX: str = "head_commit"
HEAD_KEY: str = "HEAD"


TRAVERSE_PARENT_SQL_TEMPLATE: str = """
    WITH RECURSIVE commit_ancestry(commit_id, parent_id, depth) AS (
        -- Base case: Start from the given commit_id
        SELECT commit_id, parent_id, 0 AS depth
        FROM {COMMIT_PARENT_TABLE} cg
        WHERE commit_id = ?

        UNION ALL

        -- Recursive case: Find the parent of the current commit and increment depth
        SELECT cg.commit_id, cg.parent_id, ca.depth + 1
        FROM {COMMIT_PARENT_TABLE} cg
        INNER JOIN commit_ancestry ca ON ca.parent_id = cg.commit_id
    )

    -- Select all the commits in the ancestry chain, sorted by depth
    SELECT commit_id, parent_id
    FROM commit_ancestry
    ORDER BY depth ASC;
"""


@dataclass(frozen=True)
class CommitNodeInfo:
    commit_id: CommitId
    parent_id: CommitId

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CommitNodeInfo):
            return False
        return self.commit_id == other.commit_id and self.parent_id == other.parent_id

    def __repr__(self) -> str:
        return f'CommitNodeInfo("{self.commit_id}", "{self.parent_id}")'

    def __str__(self) -> str:
        return f"Commit({self.commit_id})"


class CommitGraphStore:

    def __init__(self, notebook_id: str, graph_name: str) -> None:
        self._database_path = KishuPath.database_path(notebook_id)
        self._commit_parent_table = f"{graph_name}_{COMMIT_PARENT_TABLE_SUFFIX}"
        self._head_commit_table = f"{graph_name}_{HEAD_COMMIT_TABLE_SUFFIX}"

    def init_database(self):
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        cur.execute(f"create table if not exists {self._commit_parent_table} (commit_id text, parent_id text)")
        cur.execute(f"create table if not exists {self._head_commit_table} (head primary key, commit_id text)")
        con.commit()

    def drop_database(self):
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        cur.execute(f"drop table if exists {self._commit_parent_table}")
        cur.execute(f"drop table if exists {self._head_commit_table}")
        con.commit()

    def read_one(self, commit_id: CommitId) -> Optional[CommitNodeInfo]:
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        query = f"select commit_id, parent_id from {self._commit_parent_table} where commit_id = ?"
        try:
            cur.execute(query, (commit_id,))
            res: Optional[tuple] = cur.fetchone()
            if res is None:
                return None
            commit_id, parent_id = res
            return CommitNodeInfo(commit_id=commit_id, parent_id=parent_id)
        finally:
            con.close()

    def read_ancestry(self, commit_id: CommitId) -> List[CommitNodeInfo]:
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        query = TRAVERSE_PARENT_SQL_TEMPLATE.format(COMMIT_PARENT_TABLE=self._commit_parent_table)
        try:
            cur.execute(query, (commit_id,))
            return [CommitNodeInfo(commit_id=commit_id, parent_id=parent_id) for commit_id, parent_id in cur.fetchall()]
        finally:
            con.close()

    def read_all(self) -> List[CommitNodeInfo]:
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        query = f"select commit_id, parent_id from {self._commit_parent_table}"
        try:
            cur.execute(query)
            return [CommitNodeInfo(commit_id=commit_id, parent_id=parent_id) for commit_id, parent_id in cur.fetchall()]
        finally:
            con.close()

    def insert_parent(self, commit_node_info: CommitNodeInfo):
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        query = f"insert or replace into {self._commit_parent_table} values (?, ?)"
        cur.execute(query, (commit_node_info.commit_id, commit_node_info.parent_id))
        con.commit()

    def get_head(self) -> CommitId:
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        query = f"select commit_id from {self._head_commit_table} where head = '{HEAD_KEY}'"
        try:
            cur.execute(query)
            res: Optional[tuple] = cur.fetchone()
            if not res:
                return ABSOLUTE_PAST
            return res[0]
        finally:
            con.close()

    def set_head(self, commit_id: CommitId):
        con = sqlite3.connect(self._database_path)
        cur = con.cursor()
        query = f"insert or replace into {self._head_commit_table} values ('{HEAD_KEY}', ?)"
        cur.execute(query, (commit_id,))
        con.commit()


class KishuCommitGraph:

    def __init__(self, notebook_id: str, graph_name: str):
        self._store = CommitGraphStore(notebook_id, graph_name)

    @staticmethod
    def new_var_graph(notebook_id: str):
        return KishuCommitGraph(notebook_id, VARIABLE_GRAPH_NAME)

    @staticmethod
    def new_nb_graph(notebook_id: str):
        return KishuCommitGraph(notebook_id, NOTEBOOK_GRAPH_NAME)

    def init_database(self):
        self._store.init_database()

    def drop_database(self):
        self._store.drop_database()

    def get_commit(self, commit_id: Optional[CommitId] = None) -> Optional[CommitNodeInfo]:
        """
        Get the historical commit info given commit ID.
        """
        if commit_id is None:
            commit_id = self._store.get_head()
        return self._store.read_one(commit_id)

    def list_history(self, commit_id: Optional[CommitId] = None) -> List[CommitNodeInfo]:
        """
        Lists past commit(s) leading to the given commit.
        """
        if commit_id is None:
            commit_id = self._store.get_head()
        return self._store.read_ancestry(commit_id)

    def list_all_history(self) -> List[CommitNodeInfo]:
        """
        Lists all existing commit(s).
        """
        return self._store.read_all()

    def head(self) -> CommitId:
        """
        Get the lastest commit ID.
        """
        return self._store.get_head()

    def step(self, commit_id: CommitId) -> None:
        """
        Steps forward to the commit, associating the current commit as its past.
        """
        head_commit_id = self._store.get_head()
        self._store.insert_parent(CommitNodeInfo(commit_id, head_commit_id))
        self._store.set_head(commit_id)

    def jump(self, commit_id: CommitId) -> None:
        """
        Jumps to the given commit without associating the current commit.

        Associate with ABSOLUTE_PAST if the commit not exist before (first time seeing).
        """
        commit_node_info = self._store.read_one(commit_id)
        if commit_node_info is None:
            self._store.insert_parent(CommitNodeInfo(commit_id, ABSOLUTE_PAST))
        self._store.set_head(commit_id)
