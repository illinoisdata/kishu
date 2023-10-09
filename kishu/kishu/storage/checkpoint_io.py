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


def get_from_table(dbfile: str, table_name: str, commit_id: str) -> bytes:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select data from {} where commit_id = ?".format(table_name),
        (commit_id, )
        )
    res: tuple = cur.fetchone()
    return res[0]


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


def store_log_item(dbfile: str, commit_id: str, data: bytes) -> None:
    save_into_table(dbfile, HISTORY_LOG_TABLE, commit_id, data)


def get_log(dbfile: str) -> Dict[str, bytes]:
    log = {}
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select commit_id, data from {}".format(HISTORY_LOG_TABLE)
        )
    res = cur.fetchall()
    for key, data in res:
        log[key] = data
    return log


def get_log_item(dbfile: str, commit_id: str) -> bytes:
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    cur.execute(
        "select data from {} where commit_id = ?".format(HISTORY_LOG_TABLE),
        (commit_id, )
        )
    res: tuple = cur.fetchone()
    return res[0] if res else bytes()


def get_log_items(dbfile: str, commit_ids: List[str]) -> Dict[str, bytes]:
    """
    Returns a mapping from requested commit ID to its data. Order and completeness are not
    guaranteed (i.e. not all commit IDs may be present). Data bytes are those from store_log_item
    """
    log = {}
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    query = "select commit_id, data from {} where commit_id in ({})".format(
        HISTORY_LOG_TABLE,
        ', '.join('?' * len(commit_ids))
    )
    cur.execute(query, commit_ids)
    res = cur.fetchall()
    for key, data in res:
        log[key] = data
    return log


def get_checkpoint(dbfile: str, commit_id: str) -> bytes:
    return get_from_table(dbfile, CHECKPOINT_TABLE, commit_id)


def store_checkpoint(dbfile: str, commit_id: str, data: bytes) -> None:
    save_into_table(dbfile, CHECKPOINT_TABLE, commit_id, data)


def get_restore_plan(dbfile: str, commit_id: str) -> bytes:
    return get_from_table(dbfile, RESTORE_PLAN_TABLE, commit_id)


def store_restore_plan(dbfile: str, commit_id: str, data: bytes) -> None:
    save_into_table(dbfile, RESTORE_PLAN_TABLE, commit_id, data)
