import sqlite3

import pytest

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VariableSnapshot, VersionedName
from kishu.storage.checkpoint import CHECKPOINT_TABLE, VARIABLE_SNAPSHOT_TABLE, KishuCheckpoint
from kishu.storage.path import KishuPath


class TestKishuCheckpoint:
    @pytest.fixture
    def db_path_name(self, nb_simple_path):
        return KishuPath.database_path(nb_simple_path)

    @pytest.fixture
    def kishu_checkpoint(self, db_path_name):
        """Fixture for initializing a KishuBranch instance."""
        kishu_checkpoint = KishuCheckpoint(db_path_name)
        kishu_checkpoint.init_database()
        yield kishu_checkpoint
        kishu_checkpoint.drop_database()

    def test_create_table_no_incremental_checkpointing(self, kishu_checkpoint):
        con = sqlite3.connect(kishu_checkpoint.database_path)
        cur = con.cursor()

        # The checkpoint table should exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
        assert cur.fetchone()[0] == 1

        # The variable snapshot table should not exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_SNAPSHOT_TABLE}';")
        assert cur.fetchone()[0] == 0

    def test_create_table_with_incremental_checkpointing(self, enable_incremental_store, kishu_checkpoint):
        con = sqlite3.connect(kishu_checkpoint.database_path)
        cur = con.cursor()

        # The checkpoint table should exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
        assert cur.fetchone()[0] == 1

        # The variable snapshot table should exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_SNAPSHOT_TABLE}';")
        assert cur.fetchone()[0] == 1

    def test_store_variable_snapshots(self, enable_incremental_store, kishu_checkpoint):
        # Insert 2 variable snapshots
        empty_list = []
        empty_nested_list = [empty_list]
        kishu_checkpoint.store_variable_snapshots(
            "1",
            [VariableSnapshot(frozenset({"b", "a"}), 1), VariableSnapshot(frozenset("c"), 1)],
            Namespace({"a": empty_list, "b": empty_nested_list, "c": 1}),
        )

        # Both variable snapshots should be found.
        nameset = kishu_checkpoint.get_stored_versioned_names(["1"])
        assert nameset == {VersionedName(frozenset({"a", "b"}), 1), VersionedName(frozenset("c"), 1)}

    def test_select_variable_snapshots(self, enable_incremental_store, kishu_checkpoint):
        # Create 2 commits
        kishu_checkpoint.store_variable_snapshots("1", [VariableSnapshot(frozenset("a"), 1)], Namespace({"a": 1}))
        kishu_checkpoint.store_variable_snapshots("2", [VariableSnapshot(frozenset("b"), 1)], Namespace({"b": 2}))

        # Only the VS stored in commit 1 ("a") should be returned.
        nameset = kishu_checkpoint.get_stored_versioned_names(["1"])
        assert nameset == {VersionedName(frozenset("a"), 1)}
