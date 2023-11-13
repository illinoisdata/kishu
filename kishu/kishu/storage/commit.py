"""
Sqlite interface for storing checkpoints and other metadata.

There three types of information:
1. log: what operations were performed in the past.
2. checkpoint: the states after each operation.
3. restore plan: describes how to perform restoration.
"""
from __future__ import annotations

import dill
import enum
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional

import kishu.planning.plan

from kishu.exceptions import MissingCommitEntryError

HISTORY_TABLE = 'history'


class CommitEntryKind(str, enum.Enum):
    unspecified = "unspecified"
    jupyter = "jupyter"
    manual = "manual"


@dataclass
class FormattedCell:
    cell_type: str
    source: str
    output: Optional[str]
    execution_count: Optional[int]


@dataclass
class CommitEntry:
    """
    Records the information related to Jupyter's cell execution.

    @param execution_count  The ipython-tracked execution count, which is used for displaying
                            the cell number on Jupyter runtime.
    @param result  A printable form of the returned result (obtained by __repr__).
    @param start_time  The epoch time.
            start_time=None means that the start time is unknown, which is the case when
            the callback is first registered.
    @param end_time  The epoch time the cell execution completed.
    @param runtime_s  The difference betweeen start_time and end_time.
    @param checkpoint_runtime_s  The overhead of checkpoint operation (after the execution of
            the cell).
    @param checkpoint_vars  The variable names that are checkpointed after the cell execution.
    @param restore_plan  The checkpoint algorithm also sets this restoration plan, which
            when executed, restores all the variables as they are.
    """
    commit_id: str = ""
    kind: CommitEntryKind = CommitEntryKind.unspecified

    checkpoint_runtime_s: Optional[float] = None
    checkpoint_vars: Optional[List[str]] = None
    executed_cells: Optional[List[str]] = None
    raw_nb: Optional[str] = None
    formatted_cells: Optional[List[FormattedCell]] = None
    restore_plan: Optional[kishu.planning.plan.RestorePlan] = None
    message: str = ""
    timestamp: float = 0.0
    ahg_string: Optional[str] = None
    code_version: int = 0
    var_version: int = 0

    # Only available in jupyter commit entries
    execution_count: Optional[int] = None
    error_before_exec: Optional[str] = None
    error_in_exec: Optional[str] = None
    result: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    raw_cell: Optional[str] = None

    @property
    def runtime_s(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class KishuCommit:
    def __init__(self, dbfile: str):
        self.dbfile = dbfile

    def _get_from_table(self, table_name: str, commit_id: str) -> bytes:
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            "select data from {} where commit_id = ?".format(table_name),
            (commit_id, )
            )
        res: tuple = cur.fetchone()
        result = res[0]
        con.commit()
        return result

    def _save_into_table(self, table_name: str, commit_id: str, data: bytes) -> None:
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            "insert into {} values (?, ?)".format(table_name),
            (commit_id, memoryview(data))
        )
        con.commit()

    def init_database(self):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(f'create table if not exists {HISTORY_TABLE} (commit_id text primary key, data blob)')
        con.commit()

    def store_log_item(self, commit_entry: CommitEntry) -> None:
        self._save_into_table(HISTORY_TABLE, commit_entry.commit_id, dill.dumps(commit_entry))

    def get_log(self) -> Dict[str, bytes]:
        result = {}
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            "select commit_id, data from {}".format(HISTORY_TABLE)
            )
        res = cur.fetchall()
        for key, data in res:
            result[key] = data
        con.commit()
        return result

    def get_log_item(self, commit_id: str) -> CommitEntry:
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            "select data from {} where commit_id = ?".format(HISTORY_TABLE),
            (commit_id, )
        )
        res: tuple = cur.fetchone()
        if not res:
            raise MissingCommitEntryError(commit_id)
        result = dill.loads(res[0])
        con.commit()
        return result

    def keys_like(self, commit_id_like: str) -> List[str]:
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            "select commit_id from {} where commit_id LIKE ?".format(HISTORY_TABLE),
            (commit_id_like + "%", )
        )
        result = [commit_id for (commit_id,) in cur.fetchall()]
        con.commit()
        return result

    def get_log_items(self, commit_ids: List[str]) -> Dict[str, CommitEntry]:
        """
        Returns a mapping from requested commit ID to its data. Order and completeness are not
        guaranteed (i.e. not all commit IDs may be present). Data bytes are those from store_log_item
        """
        result = {}
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        query = "select commit_id, data from {} where commit_id in ({})".format(
            HISTORY_TABLE,
            ', '.join('?' * len(commit_ids))
        )
        cur.execute(query, commit_ids)
        res = cur.fetchall()
        for key, data in res:
            result[key] = dill.loads(data)
        con.commit()
        return result
