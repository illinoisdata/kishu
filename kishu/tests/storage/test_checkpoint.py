import sqlite3

from kishu.storage.checkpoint import CHECKPOINT_TABLE, KishuCheckpoint, VARIABLE_SNAPSHOT_TABLE
from kishu.storage.config import Config
from kishu.storage.path import KishuPath


def test_create_table():
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    con = sqlite3.connect(filename)
    cur = con.cursor()

    # The checkpoint table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
    assert cur.fetchone()[0] == 1

    # The namespace table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_SNAPSHOT_TABLE}';")
    assert cur.fetchone()[0] == 1
