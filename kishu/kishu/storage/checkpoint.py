"""
Sqlite interface for storing checkpoints.
"""

import sqlite3
from pathlib import Path
from typing import List, Set

import dill as pickle

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.storage.disk_ahg import VariableSnapshot

CHECKPOINT_TABLE = "checkpoint"
VARIABLE_SNAPSHOT_TABLE = "variable_snapshot"


class KishuCheckpoint:
    def __init__(self, database_path: Path, incremental_cr: bool = False):
        self.database_path = database_path
        self._incremental_cr = incremental_cr

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"create table if not exists {CHECKPOINT_TABLE} (commit_id text primary key, data blob)")

        # Create incremental checkpointing related tables only if incremental store is enabled.
        if self._incremental_cr:
            cur.execute(
                f"create table if not exists {VARIABLE_SNAPSHOT_TABLE} "
                f"(versioned_name text primary key, commit_id text, data blob)"
            )
        con.commit()

    def drop_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"drop table if exists {CHECKPOINT_TABLE}")
        cur.execute(f"drop table if exists {VARIABLE_SNAPSHOT_TABLE}")
        con.commit()

    def get_checkpoint(self, commit_id: str) -> bytes:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select data from {CHECKPOINT_TABLE} where commit_id = ?", (commit_id,))
        res: tuple = cur.fetchone()
        if not res:
            raise CommitIdNotExistError(commit_id)
        result = res[0]
        con.commit()
        return result

    def store_checkpoint(self, commit_id: str, data: bytes) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"insert into {CHECKPOINT_TABLE} values (?, ?)", (commit_id, memoryview(data)))
        con.commit()

    def get_variable_snapshots(self, variable_snapshots: Set[VariableSnapshot]) -> List[bytes]:
        """
        Get the data of variable snapshots.
        This function does not handle unpickling; that would be done in the RestoreActions
        as the fallback recomputation of objects is handled in those classes.
        """
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        param_list = [vs.versioned_name() for vs in variable_snapshots]
        cur.execute(
            f"select data from {VARIABLE_SNAPSHOT_TABLE} WHERE versioned_name IN (%s)" % ",".join("?" * len(param_list)),
            param_list,
        )

        res: List = cur.fetchall()
        res_list = [i[0] for i in res]
        if len(res_list) != len(variable_snapshots):
            raise ValueError(f"length of results {len(res_list)} not equal to queries {len(variable_snapshots)}:")
        return res_list

    def get_stored_versioned_names(self, commit_ids: List[str]) -> Set[str]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Get all namespaces
        cur.execute(
            f"select versioned_name from {VARIABLE_SNAPSHOT_TABLE} WHERE commit_id IN (%s)" % ",".join("?" * len(commit_ids)),
            commit_ids,
        )
        res: List = cur.fetchall()
        return set([i[0] for i in res])

    def store_variable_snapshots(self, commit_id: str, vses_to_store: List[VariableSnapshot], user_ns: Namespace) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Store each variable snapshot.
        for vs in vses_to_store:
            # Create a namespace containing only variables from the component
            ns_subset = user_ns.subset(set(vs.name))

            data_dump = pickle.dumps(ns_subset.to_dict())
            cur.execute(
                f"insert into {VARIABLE_SNAPSHOT_TABLE} values (?, ?, ?)",
                (vs.versioned_name(), commit_id, memoryview(data_dump)),
            )
            con.commit()
