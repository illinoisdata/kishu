"""
Sqlite interface for storing checkpoints.
"""

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

import dill as pickle

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.storage.disk_ahg import VariableSnapshot

CHECKPOINT_TABLE = "checkpoint"
VARIABLE_SNAPSHOT_TABLE = "variable_snapshot"
SQLITE3_DEFAULT_MAX_BLOB_SIZE = (
    500_000_000  # Compile-time maximum is 1GB, however, inserting exactly 1GB will raise the error.
)


class KishuCheckpoint:
    def __init__(self, database_path: Path, incremental_cr: bool = False):
        self.database_path = database_path
        self._incremental_cr = incremental_cr
        self._max_blob_size = SQLITE3_DEFAULT_MAX_BLOB_SIZE

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"create table if not exists {CHECKPOINT_TABLE} "
            f"(commit_id text, chunk_id int, data blob, primary key (commit_id, chunk_id))"
        )

        # Create incremental checkpointing related tables only if incremental store is enabled.
        if self._incremental_cr:
            cur.execute(
                f"create table if not exists {VARIABLE_SNAPSHOT_TABLE} "
                f"(versioned_name text, commit_id text, chunk_id int, data blob, "
                f"primary key (versioned_name, commit_id, chunk_id))"
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
        cur.execute(f"select data from {CHECKPOINT_TABLE} where commit_id = ? ORDER BY chunk_id", (commit_id,))
        res: List = cur.fetchall()
        if not res:
            raise CommitIdNotExistError(commit_id)

        con.commit()
        return b"".join([i[0] for i in res])

    def store_checkpoint(self, commit_id: str, data: bytes) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Break the blob into chunks and insert each chunk
        data_view = memoryview(data)
        for i in range(0, len(data_view), self._max_blob_size):
            chunk = data_view[i : i + self._max_blob_size]
            cur.execute(
                f"""
            INSERT INTO {CHECKPOINT_TABLE} values (?, ?, ?)
            """,
                (commit_id, i // self._max_blob_size, chunk),
            )
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
            f"select versioned_name, data from {VARIABLE_SNAPSHOT_TABLE} WHERE versioned_name IN (%s) ORDER BY chunk_id"
            % ",".join("?" * len(param_list)),
            param_list,
        )

        res: List = cur.fetchall()

        # Concatenate chunks
        chunk_dict: Dict[str, List[bytes]] = defaultdict(list)
        for versioned_name, data in res:
            chunk_dict[versioned_name].append(data)

        if len(chunk_dict) != len(variable_snapshots):
            raise ValueError(f"length of results {len(chunk_dict)} not equal to queries {len(variable_snapshots)}:")
        return [b"".join(chunk_dict[vs.versioned_name()]) for vs in variable_snapshots]

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

            try:
                data_dump = pickle.dumps(ns_subset.to_dict())
            except (pickle.PickleError, ValueError, AttributeError, TypeError):
                # If the VS fails to pickle, skip it as it would be reconstructed on (incremental) checkout.
                continue

            # Break the blob into chunks and insert each chunk
            data_view = memoryview(data_dump)
            for i in range(0, len(data_view), self._max_blob_size):
                chunk = data_view[i : i + self._max_blob_size]
                cur.execute(
                    f"""
                    INSERT INTO {VARIABLE_SNAPSHOT_TABLE} values (?, ?, ?, ?)
                    """,
                    (vs.versioned_name(), commit_id, i // self._max_blob_size, chunk),
                )
            con.commit()
