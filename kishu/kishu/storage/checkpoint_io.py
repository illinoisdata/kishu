"""
Sqlite interface for storing checkpoints and other metadata.

There three types of information:
1. log: what operations were performed in the past.
2. checkpoint: the states after each operation.
3. restore plan: describes how to perform restoration.
"""

import sqlite3
from typing import Dict, List

HISTORY_LOG_TABLE = 'history'

CHECKPOINT_TABLE = 'checkpoint'

RESTORE_PLAN_TABLE = 'restore'

BRANCH_TABLE = 'branch'

TAG_TABLE = 'tag'

VARIABLE_VERSION_TABLE = 'variable_version'

COMMIT_VARIABLE_VERSION_TABLE = 'commit_variable'


def get_from_table(dbfile: str, table_name: str, commit_id: str) -> bytes:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select data from {} where commit_id = ?".format(table_name),
        (commit_id,)
    )
    res: tuple = cur.fetchone()
    result = res[0]
    con.commit()
    return result


def save_into_table(dbfile: str, table_name: str, commit_id: str, data: bytes) -> None:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "insert into {} values (?, ?)".format(table_name),
        (commit_id, memoryview(data))
    )
    con.commit()


def init_checkpoint_database(dbfile: str):
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(f'create table if not exists {HISTORY_LOG_TABLE} (commit_id text primary key, data blob)')
    cur.execute(f'create table if not exists {CHECKPOINT_TABLE} (commit_id text primary key, data blob)')
    cur.execute(f'create table if not exists {RESTORE_PLAN_TABLE} (commit_id text primary key, data blob)')
    cur.execute(f'create table if not exists {BRANCH_TABLE} (branch_name text primary key, commit_id text)')
    cur.execute(f'create table if not exists {TAG_TABLE} (tag_name text primary key, commit_id text, message text)')

    # only when the variable is changed or newly-created will it be stored in the variable_version table
    cur.execute(
        f'create table if not exists {VARIABLE_VERSION_TABLE} (var_name text, var_commit_id text, primary key (var_name, var_commit_id))')
    cur.execute(f'create index if not exists var_name_index on {VARIABLE_VERSION_TABLE} (var_name)')

    # every variable for every commit will be stored in the commit_variable table
    cur.execute(
        f'create table if not exists {COMMIT_VARIABLE_VERSION_TABLE} (commit_id text, var_name text, var_commit_id text, primary key (var_name, commit_id))')
    cur.execute(f'create index if not exists commit_id_index on {COMMIT_VARIABLE_VERSION_TABLE} (commit_id)')


def store_log_item(dbfile: str, commit_id: str, data: bytes) -> None:
    save_into_table(dbfile, HISTORY_LOG_TABLE, commit_id, data)


def get_log(dbfile: str) -> Dict[str, bytes]:
    result = {}
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select commit_id, data from {}".format(HISTORY_LOG_TABLE)
    )
    res = cur.fetchall()
    for key, data in res:
        result[key] = data
    con.commit()
    return result


def get_log_item(dbfile: str, commit_id: str) -> bytes:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select data from {} where commit_id = ?".format(HISTORY_LOG_TABLE),
        (commit_id,)
    )
    res: tuple = cur.fetchone()
    result = res[0] if res else bytes()
    con.commit()
    return result


def keys_like(dbfile: str, commit_id_like: str) -> List[str]:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select commit_id from {} where commit_id LIKE ?".format(HISTORY_LOG_TABLE),
        (commit_id_like + "%",)
    )
    result = [commit_id for (commit_id,) in cur.fetchall()]
    con.commit()
    return result


def get_log_items(dbfile: str, commit_ids: List[str]) -> Dict[str, bytes]:
    """
    Returns a mapping from requested commit ID to its data. Order and completeness are not
    guaranteed (i.e. not all commit IDs may be present). Data bytes are those from store_log_item
    """
    result = {}
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    query = "select commit_id, data from {} where commit_id in ({})".format(
        HISTORY_LOG_TABLE,
        ', '.join('?' * len(commit_ids))
    )
    cur.execute(query, commit_ids)
    res = cur.fetchall()
    for key, data in res:
        result[key] = data
    con.commit()
    return result


def get_checkpoint(dbfile: str, commit_id: str) -> bytes:
    return get_from_table(dbfile, CHECKPOINT_TABLE, commit_id)


def store_checkpoint(dbfile: str, commit_id: str, data: bytes) -> None:
    save_into_table(dbfile, CHECKPOINT_TABLE, commit_id, data)


def get_restore_plan(dbfile: str, commit_id: str) -> bytes:
    return get_from_table(dbfile, RESTORE_PLAN_TABLE, commit_id)


def store_restore_plan(dbfile: str, commit_id: str, data: bytes) -> None:
    save_into_table(dbfile, RESTORE_PLAN_TABLE, commit_id, data)


def store_variable_version_table(dbfile: str, var_names: set[str], commit_id: str):
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    for var_name in var_names:
        cur.execute(
            "insert into {} values (?, ?)".format(VARIABLE_VERSION_TABLE),
            (var_name, commit_id)
        )
    con.commit()


def store_commit_variable_version_table(dbfile: str, commit_id: str, commit_variable_version_map: Dict[str, str]):
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    for key, value in commit_variable_version_map.items():
        cur.execute(
            "insert into {} values (?, ?, ?)".format(COMMIT_VARIABLE_VERSION_TABLE),
            (commit_id, key, value)
        )
    con.commit()


def get_variable_version_by_commit_id(dbfile: str, commit_id: str) -> Dict[str, str]:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select var_name, var_commit_id from {} where commit_id = ?".format(COMMIT_VARIABLE_VERSION_TABLE),
        (commit_id,)
    )
    res = cur.fetchall()
    result = {}
    for var_name, var_commit_id in res:
        result[var_name] = var_commit_id
    con.commit()
    return result


def get_commit_ids_by_variable_name(dbfile: str, variable_name: str) -> List[str]:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    print("var_name", variable_name)
    print("select var_commit_id from {} where var_name = ?".format(VARIABLE_VERSION_TABLE),
        (variable_name))
    cur.execute(
        "select var_commit_id from {} where var_name = ?".format(VARIABLE_VERSION_TABLE),
        (variable_name,)
    )
    res = cur.fetchall()
    result = []
    for var_commit_id in res:
        result.append(var_commit_id)
    con.commit()
    return result
