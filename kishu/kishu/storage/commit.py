"""
Sqlite interface for storing checkpoints and other metadata.

There three types of information:
1. log: what operations were performed in the past.
2. checkpoint: the states after each operation.
3. restore plan: describes how to perform restoration.
"""

from __future__ import annotations

import enum
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import dill

import kishu.planning.plan
from kishu.exceptions import MissingCommitEntryError

COMMIT_ENTRY_TABLE = "commit_entry"


class CommitEntryKind(str, enum.Enum):
    unspecified = "unspecified"
    jupyter = "jupyter"
    manual = "manual"


class NotebookCommitState(str, enum.Enum):
    """State of notebook commit. The state machine diagram is as followed.

    unspecified --> with_commit --> updated

    unspecified: no notebook commit.
    with_commit: the notebook is recorded at same time as commit creation.
    amend_notebook: the notebook is separately amended to the commit.

    """

    unspecified = "unspecified"
    with_commit = "with_commit"
    amend_notebook = "amend_notebook"


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
    message: str = ""
    timestamp: float = 0.0
    kind: CommitEntryKind = CommitEntryKind.unspecified

    # Execution state.
    executed_cells: Optional[List[str]] = None
    executed_outputs: Optional[Dict[int, str]] = None

    # Notebook state.
    raw_nb: Optional[str] = None
    formatted_cells: Optional[List[FormattedCell]] = None
    nb_record_type: NotebookCommitState = NotebookCommitState.unspecified

    # Planner state.
    restore_plan: Optional[kishu.planning.plan.RestorePlan] = None
    checkpoint_runtime_s: Optional[float] = None

    # Version hashes.
    code_version: int = 0
    varset_version: int = 0

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
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"create table if not exists {COMMIT_ENTRY_TABLE} (commit_id text primary key, data blob)")
        con.commit()

    def store_commit(self, commit_entry: CommitEntry) -> None:
        commit_entry_dill = dill.dumps(commit_entry)
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"insert into {COMMIT_ENTRY_TABLE} values (?, ?)", (commit_entry.commit_id, memoryview(commit_entry_dill)))
        con.commit()

    def update_commit(self, commit_entry: CommitEntry) -> None:
        commit_entry_dill = dill.dumps(commit_entry)
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"update {COMMIT_ENTRY_TABLE} set data = ? where commit_id = ?",
            (memoryview(commit_entry_dill), commit_entry.commit_id),
        )
        con.commit()

    def get_commit(self, commit_id: str) -> CommitEntry:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select data from {COMMIT_ENTRY_TABLE} where commit_id = ?", (commit_id,))
        res: tuple = cur.fetchone()
        if not res:
            raise MissingCommitEntryError(commit_id)
        result = dill.loads(res[0])
        con.commit()
        return result

    def get_commits(self, commit_ids: List[str]) -> Dict[str, CommitEntry]:
        """
        Returns a mapping from requested commit ID to its data. Order and completeness are not
        guaranteed (i.e. not all commit IDs may be present). Data bytes are those from store_commit
        """
        result = {}
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select commit_id, data from {COMMIT_ENTRY_TABLE} " f"where commit_id in ({', '.join('?' * len(commit_ids))})"
        cur.execute(query, commit_ids)
        res = cur.fetchall()
        for key, data in res:
            result[key] = dill.loads(data)
        con.commit()
        return result

    def keys_like(self, commit_id_like: str) -> List[str]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select commit_id from {COMMIT_ENTRY_TABLE} where commit_id LIKE ?", (commit_id_like + "%",))
        result = [commit_id for (commit_id,) in cur.fetchall()]
        con.commit()
        return result
