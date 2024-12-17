import pickle
import sqlite3

import pytest

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VariableSnapshot
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
        kishu_checkpoint._max_blob_size = 1000  # 1KB
        yield kishu_checkpoint
        kishu_checkpoint.drop_database()

    @pytest.fixture
    def kishu_incremental_checkpoint(self, db_path_name):
        """Fixture for initializing a KishuBranch instance with incremental CR."""
        kishu_incremental_checkpoint = KishuCheckpoint(db_path_name, incremental_cr=True)
        kishu_incremental_checkpoint.init_database()
        kishu_incremental_checkpoint._max_blob_size = 1000  # 1KB
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

        vs_ab = VariableSnapshot(frozenset({"b", "a"}), 1)
        vs_c = VariableSnapshot(frozenset("c"), 1)
        kishu_incremental_checkpoint.store_variable_snapshots(
            "1",
            [vs_ab, vs_c],
            Namespace({"a": empty_list, "b": empty_nested_list, "c": 1}),
        )

        # Both variable snapshots should be found.
        nameset = kishu_incremental_checkpoint.get_stored_versioned_names(["1"])
        assert nameset == {vs_ab.versioned_name(), vs_c.versioned_name()}

    def test_get_stored_versioned_names(self, kishu_incremental_checkpoint):
        # Create 2 commits
        vs_a = VariableSnapshot(frozenset("a"), 1)
        vs_b = VariableSnapshot(frozenset("b"), 1)

        kishu_incremental_checkpoint.store_variable_snapshots("1", [vs_a], Namespace({"a": 1}))
        kishu_incremental_checkpoint.store_variable_snapshots("2", [vs_b], Namespace({"b": 2}))

        # Only the VS stored in commit 1 ("a") should be returned.
        nameset = kishu_incremental_checkpoint.get_stored_versioned_names(["1"])
        assert nameset == {vs_a.versioned_name()}

    def test_get_variable_snapshots(self, kishu_incremental_checkpoint):
        # Create 2 commits; first has 2 VSes, second has 1.
        empty_list = []
        empty_nested_list = [empty_list]

        vs_ab = VariableSnapshot(frozenset({"b", "a"}), 1)
        vs_c = VariableSnapshot(frozenset("c"), 1)
        vs_b = VariableSnapshot(frozenset("b"), 2)

        kishu_incremental_checkpoint.store_variable_snapshots(
            "1",
            [vs_ab, vs_c],
            Namespace({"a": empty_list, "b": empty_nested_list, "c": "strc"}),
        )
        kishu_incremental_checkpoint.store_variable_snapshots("2", [vs_b], Namespace({"b": "strb"}))

        data_list = kishu_incremental_checkpoint.get_variable_snapshots([vs_c, vs_b])

        # Returned data is sorted in the same order as the passed in versioned names.
        unpickled_data_list = [pickle.loads(i) for i in data_list]
        assert unpickled_data_list[0] == {"c": "strc"}
        assert unpickled_data_list[1] == {"b": "strb"}

    def test_chunking(self, kishu_checkpoint):
        test_str = b"A" * 1500  # 1.5KB, expect 2 chunks
        kishu_checkpoint.store_checkpoint("1", test_str)

        # The checkpoint table should contain 2 entries.
        con = sqlite3.connect(kishu_checkpoint.database_path)
        cur = con.cursor()
        cur.execute(f"SELECT count(*) FROM {CHECKPOINT_TABLE};")
        assert cur.fetchone()[0] == 2

        assert kishu_checkpoint.get_checkpoint("1") == test_str

    def test_chunking_single(self, kishu_incremental_checkpoint):
        vs_a = VariableSnapshot(frozenset({"a"}), 1)

        test_str = "A" * 1500  # 1.5KB, expect 2 chunks
        kishu_incremental_checkpoint.store_variable_snapshots(
            "1",
            [vs_a],
            Namespace({"a": test_str}),
        )

        # The incremental checkpoint table should contain 2 entries.
        con = sqlite3.connect(kishu_incremental_checkpoint.database_path)
        cur = con.cursor()
        cur.execute(f"SELECT count(*) FROM {VARIABLE_SNAPSHOT_TABLE};")
        assert cur.fetchone()[0] == 2

        data_list = kishu_incremental_checkpoint.get_variable_snapshots([vs_a])

        unpickled_data_list = [pickle.loads(i) for i in data_list]
        assert unpickled_data_list[0] == {"a": test_str}

    def test_chunking_multiple(self, kishu_incremental_checkpoint):
        vs_a = VariableSnapshot(frozenset({"a"}), 1)
        vs_b = VariableSnapshot(frozenset({"b"}), 1)

        test_stra = "A" * 1500  # 1.5KB, expect 2 chunks
        test_strb = "B" * 2500  # 2.5KB, expect 3 chunks
        kishu_incremental_checkpoint.store_variable_snapshots(
            "1",
            [vs_a, vs_b],
            Namespace({"a": test_stra, "b": test_strb}),
        )

        # The incremental checkpoint table should contain 5 entries (2 for A + 3 for B).
        con = sqlite3.connect(kishu_incremental_checkpoint.database_path)
        cur = con.cursor()
        cur.execute(f"SELECT count(*) FROM {VARIABLE_SNAPSHOT_TABLE};")
        assert cur.fetchone()[0] == 5

        data_list = kishu_incremental_checkpoint.get_variable_snapshots([vs_a, vs_b])

        # Returned data is sorted in the same order as the passed in versioned names.
        unpickled_data_list = [pickle.loads(i) for i in data_list]
        assert unpickled_data_list[0] == {"a": test_stra}
        assert unpickled_data_list[1] == {"b": test_strb}

    def test_skip_unserializable(self, kishu_incremental_checkpoint):
        vs_gen = VariableSnapshot(frozenset({"gen"}), 1)
        vs_string = VariableSnapshot(frozenset({"str"}), 1)

        gen = (i for i in range(10))
        string = "A" * 100
        kishu_incremental_checkpoint.store_variable_snapshots(
            "1",
            [vs_gen, vs_string],
            Namespace({"gen": gen, "str": string}),
        )

        # Only vs_string would be returned (as vs_gen was skipped due to not being serializable).
        nameset = kishu_incremental_checkpoint.get_stored_versioned_names(["1"])
        assert nameset == {vs_string.versioned_name()}
