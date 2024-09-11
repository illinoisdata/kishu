import sqlite3

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VariableSnapshot, VersionedName
from kishu.storage.checkpoint import CHECKPOINT_TABLE, KishuCheckpoint, VARIABLE_SNAPSHOT_TABLE
from kishu.storage.config import Config
from kishu.storage.path import KishuPath


def test_create_table_no_incremental_checkpointing():
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    con = sqlite3.connect(filename)
    cur = con.cursor()

    # The checkpoint table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
    assert cur.fetchone()[0] == 1

    # The variable snapshot table should not exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_SNAPSHOT_TABLE}';")
    assert cur.fetchone()[0] == 0


def test_create_table_with_incremental_checkpointing():
    Config.set("PLANNER", "incremental_store", True)

    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    con = sqlite3.connect(filename)
    cur = con.cursor()

    # The checkpoint table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
    assert cur.fetchone()[0] == 1

    # The variable snapshot table should exist.
    cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_SNAPSHOT_TABLE}';")
    assert cur.fetchone()[0] == 1


def test_store_variable_snapshots():
    Config.set('PLANNER', 'incremental_store', True)

    filename = KishuPath.database_path("test")
    kishu_checkpoint = KishuCheckpoint(filename)
    kishu_checkpoint.init_database()

    # Insert 2 variable snapshots
    empty_list = []
    empty_nested_list = [empty_list]
    kishu_checkpoint.store_variable_snapshots(
        "1",
        [VariableSnapshot(frozenset({"b", "a"}), 1), VariableSnapshot(frozenset("c"), 1)],
        Namespace({"a": empty_list, "b": empty_nested_list, "c": 1})
    )

    # Both variable snapshots should be found.
    nameset = kishu_checkpoint.get_stored_versioned_names(["1"])
    assert nameset == {VersionedName(frozenset({"a", "b"}), 1), VersionedName(frozenset("c"), 1)}


def test_select_variable_snapshots():
    Config.set('PLANNER', 'incremental_store', True)

    filename = KishuPath.database_path("test")
    kishu_checkpoint = KishuCheckpoint(filename)
    kishu_checkpoint.init_database()

    # Create 2 commits
    kishu_checkpoint.store_variable_snapshots(
        "1",
        [VariableSnapshot(frozenset("a"), 1)],
        Namespace({"a": 1})
    )
    kishu_checkpoint.store_variable_snapshots(
        "2",
        [VariableSnapshot(frozenset("b"), 1)],
        Namespace({"b": 2})
    )

    # Only the VS stored in commit 1 ("a") should be returned.
    nameset = kishu_checkpoint.get_stored_versioned_names(["1"])
    assert nameset == {VersionedName(frozenset("a"), 1)}
