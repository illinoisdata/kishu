"""
Sqlite interface for storing checkpoints.
"""

import sqlite3
import uuid
from pathlib import Path
from typing import List, Set

import dill as pickle

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VariableName, VariableSnapshot, VersionedName
from kishu.storage.config import Config

CHECKPOINT_TABLE = "checkpoint"
VARIABLE_SNAPSHOT_TABLE = "variable_snapshot"


class KishuCheckpoint:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"create table if not exists {CHECKPOINT_TABLE} (commit_id text primary key, data blob)")

        # Create incremental checkpointing related tables only if the config flag is enabled.
        if Config.get("PLANNER", "incremental_store", False):
            cur.execute(
                f"create table if not exists {VARIABLE_SNAPSHOT_TABLE} " f"(version int, name text, commit_id text, data blob)"
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

    def get_stored_versioned_names(self, commit_ids: List[str]) -> Set[VersionedName]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Get all namespaces
        cur.execute(
            f"select version, name from {VARIABLE_SNAPSHOT_TABLE} WHERE commit_id IN (%s)" % ",".join("?" * len(commit_ids)),
            commit_ids,
        )
        res: List = cur.fetchall()
        return {VersionedName(KishuCheckpoint.decode_name(name), version) for version, name in res}

    def store_variable_snapshots(self, commit_id: str, vses_to_store: List[VariableSnapshot], user_ns: Namespace) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Store each variable snapshot.
        for vs in vses_to_store:
            # Create a namespace containing only variables from the component
            ns_subset = user_ns.subset(set(vs.name))

            data_dump = pickle.dumps(ns_subset.to_dict())
            cur.execute(
                f"insert into {VARIABLE_SNAPSHOT_TABLE} values (?, ?, ?, ?)",
                (vs.version, KishuCheckpoint.encode_name(vs.name), commit_id, memoryview(data_dump)),
            )
            con.commit()

    @staticmethod
    def encode_name(variable_name: VariableName) -> str:
        return repr(sorted(variable_name))

    @staticmethod
    def decode_name(encoded_name: str) -> VariableName:
        return frozenset([name.strip().replace("'", "") for name in encoded_name.replace("[", "").replace("]", "").split(",")])
