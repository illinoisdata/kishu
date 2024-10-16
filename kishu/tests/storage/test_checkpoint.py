import sqlite3

from kishu.storage.checkpoint import CHECKPOINT_TABLE, KishuCheckpoint, NAMESPACE_TABLE, VARIABLE_KV_TABLE
from kishu.storage.config import Config
from kishu.storage.path import KishuPath


def test_create_table_no_incremental_checkpointing(nb_simple_path):
    database_path = KishuPath.database_path(nb_simple_path)
    KishuCheckpoint(database_path).init_database()

    con = sqlite3.connect(database_path)
    cur = con.cursor()

    # The checkpoint table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
    assert cur.fetchone()[0] == 1

    # The namespace table should not exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{NAMESPACE_TABLE}';")
    assert cur.fetchone()[0] == 0

    # The variable KV table should not exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_KV_TABLE}';")
    assert cur.fetchone()[0] == 0


def test_create_table_with_incremental_checkpointing(nb_simple_path):
    Config.set("PLANNER", "incremental_store", True)

    database_path = KishuPath.database_path(nb_simple_path)
    KishuCheckpoint(database_path).init_database()

    con = sqlite3.connect(database_path)
    cur = con.cursor()

    # The checkpoint table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
    assert cur.fetchone()[0] == 1

    # The namespace table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{NAMESPACE_TABLE}';")
    assert cur.fetchone()[0] == 1

    # The variable KV table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_KV_TABLE}';")
    assert cur.fetchone()[0] == 1
