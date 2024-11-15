import pickle
import pytest
import sqlite3

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

    @pytest.fixture
    def kishu_incremental_checkpoint(self, db_path_name):
        """Fixture for initializing a KishuBranch instance with incremental CR."""
        kishu_incremental_checkpoint = KishuCheckpoint(db_path_name)
        kishu_incremental_checkpoint.init_database(incremental_store=True)
        yield kishu_incremental_checkpoint
        kishu_incremental_checkpoint.drop_database()

    def test_create_table_no_incremental_checkpointing(self, kishu_checkpoint):
        con = sqlite3.connect(kishu_checkpoint.database_path)
        cur = con.cursor()

        # The checkpoint table should exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
        assert cur.fetchone()[0] == 1

        # The variable snapshot table should not exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_SNAPSHOT_TABLE}';")
        assert cur.fetchone()[0] == 0

    def test_create_table_with_incremental_checkpointing(self, kishu_incremental_checkpoint):
        con = sqlite3.connect(kishu_incremental_checkpoint.database_path)
        cur = con.cursor()

        # The checkpoint table should exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{CHECKPOINT_TABLE}';")
        assert cur.fetchone()[0] == 1

        # The variable snapshot table should exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{VARIABLE_SNAPSHOT_TABLE}';")
        assert cur.fetchone()[0] == 1

    def test_store_variable_snapshots(self, kishu_incremental_checkpoint):
        # Insert 2 variable snapshots
        empty_list = []
        empty_nested_list = [empty_list]
        kishu_incremental_checkpoint.store_variable_snapshots(
            "1",
            [VariableSnapshot(frozenset({"b", "a"}), 1), VariableSnapshot(frozenset("c"), 1)],
            Namespace({"a": empty_list, "b": empty_nested_list, "c": 1}),
        )

        # Both variable snapshots should be found.
        nameset = kishu_incremental_checkpoint.get_stored_versioned_names(["1"])
        assert nameset == {VersionedName(frozenset({"a", "b"}), 1), VersionedName(frozenset("c"), 1)}

    def test_get_stored_versioned_names(self, kishu_incremental_checkpoint):
        # Create 2 commits
        kishu_incremental_checkpoint.store_variable_snapshots("1", [VariableSnapshot(frozenset("a"), 1)], Namespace({"a": 1}))
        kishu_incremental_checkpoint.store_variable_snapshots("2", [VariableSnapshot(frozenset("b"), 2)], Namespace({"b": 2}))

        # Only the VS stored in commit 1 ("a") should be returned.
        nameset = kishu_incremental_checkpoint.get_stored_versioned_names(["1"])
        assert nameset == {VersionedName(frozenset("a"), 1)}

    def test_get_variable_snapshots(self, kishu_incremental_checkpoint):
        # Create 2 commits; first has 2 VSes, second has 1.
        empty_list = []
        empty_nested_list = [empty_list]
        kishu_incremental_checkpoint.store_variable_snapshots(
            "1",
            [VariableSnapshot(frozenset({"b", "a"}), 1), VariableSnapshot(frozenset("c"), 1)],
            Namespace({"a": empty_list, "b": empty_nested_list, "c": "strc"}),
        )
        kishu_incremental_checkpoint.store_variable_snapshots(
            "2", [VariableSnapshot(frozenset("b"), 2)], Namespace({"b": "strb"})
        )

        data_list = kishu_incremental_checkpoint.get_variable_snapshots([VersionedName("c", 1), VersionedName("b", 2)])

        # Returned data is sorted in the same order as the passed in versioned names.
        unpickled_data_list = [pickle.loads(i) for i in data_list]
        assert unpickled_data_list[0] == {"c": "strc"}
        assert unpickled_data_list[1] == {"b": "strb"}
