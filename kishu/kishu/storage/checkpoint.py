"""
Sqlite interface for storing checkpoints.
"""
import dill as pickle
import sqlite3
import uuid

from typing import List

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VersionedName, VsConnectedComponents
from kishu.storage.config import Config


CHECKPOINT_TABLE = 'checkpoint'
VARIABLE_KV_TABLE = 'variable_kv'
NAMESPACE_TABLE = 'namespace'


class KishuCheckpoint:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f'create table if not exists {CHECKPOINT_TABLE} (commit_id text primary key, data blob)')

        # Create incremental checkpointing related tables only if the config flag is enabled.
        if Config.get('PLANNER', 'incremental_store', False):
            cur.execute(f'create table if not exists {VARIABLE_KV_TABLE} (version int, name text, ns_id text, commit_id text)')
            cur.execute(f'create table if not exists {NAMESPACE_TABLE} (ns_id text primary key, data blob)')

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

    def get_stored_connected_components(self) -> VsConnectedComponents:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Get all namespaces
        cur.execute(f"select distinct ns_id from {VARIABLE_KV_TABLE}")
        select_distinct_res: List = cur.fetchall()

        component_list = []
        for ns_id in select_distinct_res:
            cur.execute(
                f"select version, name from {VARIABLE_KV_TABLE} where ns_id = ?",
                ns_id
            )
            filter_res: List = cur.fetchall()
            component_list.append([VersionedName(i[1], i[0]) for i in filter_res])

        return VsConnectedComponents.create_from_component_list(component_list)

    def store_variable_kv(self, commit_id: str, vs_connected_components: VsConnectedComponents, user_ns: Namespace) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Store each linked variable component
        for component in vs_connected_components.get_connected_components():
            # Create a namespace containing only variables from the component
            ns_subset = user_ns.subset(set(i.name for i in component))
            ns_id = uuid.uuid4().hex

            # Insert the mapping from variable KVs to namespace into database.
            cur.executemany(
                f"insert into {VARIABLE_KV_TABLE} values (?, ?, ?, ?)",
                [(versioned_name.version, versioned_name.name, commit_id, ns_id) for versioned_name in component]
            )
            con.commit()

            # Insert namespace to data mapping into database
            cur.execute(
                f"insert into {NAMESPACE_TABLE} values (?, ?)",
                (ns_id, memoryview(pickle.dumps(ns_subset)))
            )
            con.commit()
