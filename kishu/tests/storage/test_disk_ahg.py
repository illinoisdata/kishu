import sqlite3
from typing import Generator

import pytest

from kishu.jupyter.namespace import Namespace
from kishu.storage.config import Config
from kishu.storage.disk_ahg import (
    AHG_ACTIVE_VSES_TABLE,
    AHG_CE_INPUT_TABLE,
    AHG_CE_OUTPUT_TABLE,
    AHG_CELL_EXECUTION_TABLE,
    AHG_VARIABLE_SNAPSHOT_TABLE,
    AHGUpdateResult,
    CellExecution,
    KishuDiskAHG,
    VariableSnapshot,
)
from kishu.storage.path import KishuPath


class TestDiskAHG:
    @pytest.fixture
    def db_path_name(self, nb_simple_path):
        return KishuPath.database_path(nb_simple_path)

    @pytest.fixture
    def kishu_disk_ahg(self, db_path_name):
        """Fixture for initializing a KishuBranch instance."""
        kishu_disk_ahg = KishuDiskAHG(db_path_name)
        kishu_disk_ahg.init_database()
        yield kishu_disk_ahg
        kishu_disk_ahg.drop_database()

    def test_create_tables(self, kishu_disk_ahg):
        con = sqlite3.connect(kishu_disk_ahg.database_path)
        cur = con.cursor()

        # All tables should exist.
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{AHG_VARIABLE_SNAPSHOT_TABLE}';")
        assert cur.fetchone()[0] == 1

        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{AHG_CELL_EXECUTION_TABLE}';")
        assert cur.fetchone()[0] == 1

        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{AHG_CE_INPUT_TABLE}';")
        assert cur.fetchone()[0] == 1

        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{AHG_CE_OUTPUT_TABLE}';")
        assert cur.fetchone()[0] == 1

        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{AHG_ACTIVE_VSES_TABLE}';")
        assert cur.fetchone()[0] == 1

    def test_disk_ahg(self, kishu_disk_ahg):
        """
        Store a few commits corresponding to this test graph.
        (cost:2) "x"  "y" (cost: 2)
             c3   |    |  c2
                 "z" "z"
                   "z"
                    | c1 (cost: 3)
                   []
        """
        # Variable snapshots
        vs1 = VariableSnapshot(frozenset("x"), 1, deleted=False, size=2)
        vs2 = VariableSnapshot(frozenset("y"), 2, deleted=False, size=2)
        vs3 = VariableSnapshot(frozenset("z"), 3, deleted=False, size=2)
        vs1_deleted = VariableSnapshot(frozenset("x"), 3, deleted=True, size=0)

        # Cells
        ce1 = CellExecution(1, "x = 1", 3.0)
        ce2 = CellExecution(2, "y = x + 1", 0.1)
        ce3 = CellExecution(3, "z = x + 2\n del x", 0.1)

        # Cell 1
        kishu_disk_ahg.store_update_results(
            AHGUpdateResult(commit_id="1:1", accessed_vss=[], output_vss=[vs1], newest_ce=ce1, active_vss=[vs1])
        )

        # Cell 2
        kishu_disk_ahg.store_update_results(
            AHGUpdateResult(commit_id="1:2", accessed_vss=[vs1], output_vss=[vs2], newest_ce=ce2, active_vss=[vs1, vs2])
        )

        # Cell 3
        kishu_disk_ahg.store_update_results(
            AHGUpdateResult(
                commit_id="1:3",
                accessed_vss=[vs1],
                output_vss=[vs1_deleted, vs3],
                newest_ce=ce3,
                active_vss=[vs2, vs3],  # vs1 (x) was deleted here
            )
        )

        # All variable snapshots.
        assert set(kishu_disk_ahg.get_all_variable_snapshots()) == {vs1, vs2, vs3, vs1_deleted}

        # All cell executions.
        assert set(kishu_disk_ahg.get_all_cell_executions()) == {ce1, ce2, ce3}

        # Primary key to object mappings.
        assert kishu_disk_ahg.get_ce_by_cell_num(1) == ce1
        assert set(kishu_disk_ahg.get_vs_by_versioned_names([vs1.versioned_name(), vs2.versioned_name()])) == {vs1, vs2}

        # VS/CE edges.
        assert kishu_disk_ahg.get_vs_input_ce(vs1) == ce1
        assert set(kishu_disk_ahg.get_ce_input_vses(ce2)) == {vs1}
        assert set(kishu_disk_ahg.get_ce_output_vses(ce2)) == {vs2}

        # Active VSes.
        assert set(kishu_disk_ahg.get_active_vses("1:3")) == {vs2, vs3}


class TestProfiling:
    @pytest.fixture()
    def disable_always_migrate_recompute(self, tmp_kishu_path) -> Generator[type, None, None]:
        prev_value_migrate = Config.get("OPTIMIZER", "always_migrate", False)
        prev_value_recompute = Config.get("OPTIMIZER", "always_migrate", False)
        Config.set("OPTIMIZER", "always_migrate", False)
        Config.set("OPTIMIZER", "always_recompute", False)
        yield Config
        Config.set("OPTIMIZER", "always_migrate", prev_value_migrate)
        Config.set("OPTIMIZER", "always_recompute", prev_value_recompute)

    @pytest.fixture()
    def enable_always_migrate(self, tmp_kishu_path) -> Generator[type, None, None]:
        prev_value = Config.get("OPTIMIZER", "always_migrate", False)
        Config.set("OPTIMIZER", "always_migrate", True)
        yield Config
        Config.set("OPTIMIZER", "always_migrate", prev_value)

    @pytest.fixture()
    def enable_always_recompute(self, tmp_kishu_path) -> Generator[type, None, None]:
        prev_value = Config.get("OPTIMIZER", "always_recompute", False)
        Config.set("OPTIMIZER", "always_recompute", True)
        yield Config
        Config.set("OPTIMIZER", "always_recompute", prev_value)

    def test_with_profiling(self, disable_always_migrate_recompute):
        user_ns = Namespace({"x": "A" * 100})
        vs_no_disabled = VariableSnapshot.select_names_from_update(user_ns, 1, frozenset("x"))
        assert vs_no_disabled.size > 1.0

    def test_disable_profiling_always_migrate(self, enable_always_migrate):
        user_ns = Namespace({"x": "A" * 100})
        vs_disabled = VariableSnapshot.select_names_from_update(user_ns, 1, frozenset("x"))
        assert vs_disabled.size == 1.0

    def test_disable_profiling_always_recompute(self, enable_always_recompute):
        user_ns = Namespace({"x": "A" * 100})
        vs_disabled = VariableSnapshot.select_names_from_update(user_ns, 1, frozenset("x"))
        assert vs_disabled.size == 1.0
