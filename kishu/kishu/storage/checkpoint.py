"""
Sqlite interface for storing checkpoints.
"""
import ast
import dill as pickle
import sqlite3
import sys

from typing import Dict, FrozenSet, List, Set, Tuple

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VariableSnapshot, VersionedName, VersionedNameContext
from kishu.storage.config import Config


CHECKPOINT_TABLE = 'checkpoint'
VARIABLE_SNAPSHOT_TABLE = 'variable_snapshot'


class KishuCheckpoint:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f'create table if not exists {CHECKPOINT_TABLE} (commit_id text primary key, data blob)')

        # Create incremental checkpointing related tables only if the config flag is enabled.
        if Config.get('PLANNER', 'incremental_cr', False):
            cur.execute(f'create table if not exists {VARIABLE_SNAPSHOT_TABLE} '
                        f'(version int, name text, commit_id text, size int, data blob)')

        con.commit()

    def get_checkpoint(self, commit_id: str) -> bytes:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"select data from {CHECKPOINT_TABLE} where commit_id = ?",
            (commit_id, )
        )
        res: tuple = cur.fetchone()
        if not res:
            raise CommitIdNotExistError(commit_id)
        result = res[0]
        con.commit()
        return result

    def store_checkpoint(self, commit_id: str, data: bytes) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"insert into {CHECKPOINT_TABLE} values (?, ?)",
            (commit_id, memoryview(data))
        )
        con.commit()

    def get_variable_snapshots(self, versioned_names: List[Tuple[VersionedName, VersionedNameContext]]) -> List[bytes]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        param_list = [(vn.version, repr(set(vn.name)), vnc.commit_id) for vn, vnc in versioned_names]
        print("get variable snapshot:", param_list)
        cur.execute(
            f"""select data from {VARIABLE_SNAPSHOT_TABLE} where (version, name, commit_id) IN (VALUES {','.join(f'({",".join("?" * len(t))})' for t in param_list)})""", [i for t in param_list for i in t])
        res: List = cur.fetchall()
        return [i[0] for i in res]

    def get_stored_versioned_names(self, commit_ids: List[str]) -> Dict[VersionedName, VersionedNameContext]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Get all namespaces
        cur.execute(f"select version, name, size, commit_id from {VARIABLE_SNAPSHOT_TABLE} WHERE commit_id IN (%s)" %
                           ','.join('?'*len(commit_ids)), commit_ids)
        res: List = cur.fetchall()
        return {VersionedName(frozenset(ast.literal_eval(i[1])), i[0]): VersionedNameContext(i[2], i[3]) for i in res}

    def store_variable_snapshots(self, commit_id: str, vses_to_store: List[VariableSnapshot], user_ns: Namespace) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Store each variable snapshot.
        for vs in vses_to_store:
            # Create a namespace containing only variables from the component
            ns_subset = user_ns.subset(set(vs.name))

            data_dump = pickle.dumps(ns_subset)
            cur.execute(
                f"insert into {VARIABLE_SNAPSHOT_TABLE} values (?, ?, ?, ?, ?)",
                (vs.version, repr(set(vs.name)), commit_id, sys.getsizeof(data_dump), memoryview(data_dump))
            )
            con.commit()
