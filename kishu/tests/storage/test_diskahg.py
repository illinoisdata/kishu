import pytest
import sqlite3

from kishu.planning.ahg import AHG, AHGUpdateInfo
from kishu.storage.diskahg import (
    AHG_CELL_EXECUTION_TABLE,
    AHG_CE_INPUT_TABLE,
    AHG_CE_OUTPUT_TABLE,
    AHG_VARIABLE_SNAPSHOT_TABLE,
    KishuDiskAHG,
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

    def test_store_ahg(self, kishu_disk_ahg):
        ahg = AHG()

        # x and y are created
        update_result = ahg.update_graph(AHGUpdateInfo(version=1, cell_runtime_s=1.0, current_variables={"x", "y"}))
        kishu_disk_ahg.store_update_results(update_result)

        # x is read and modified, z is created, y is deleted
        update_result = ahg.update_graph(
            AHGUpdateInfo(
                version=2,
                cell_runtime_s=1.0,
                accessed_variables={"x"},
                current_variables={"x", "z"},
                modified_variables={"x"},
                deleted_variables={"y"},
            )
        )
        kishu_disk_ahg.store_update_results(update_result)

        assert len(kishu_disk_ahg.get_variable_snapshots()) == 5  # 2 versions of x + 2 versions of y + 1 version of z
        assert len(kishu_disk_ahg.get_cell_executions()) == 2
        assert len(kishu_disk_ahg.get_vs_to_ce_edges()) == 1  # cell 2 accesses x
        assert len(kishu_disk_ahg.get_ce_to_vs_edges()) == 5  # cell 1 creates x and y, cell 2 creates x, y, and z

        # # Check contents of AHG are correct

        # assert len(new_ahg.get_cell_executions()) == 2

        # # Check links between AHG contents are correct
        # assert len(new_ahg.get_cell_executions()[1].src_vss) == 1
        # assert len(new_ahg.get_cell_executions()[1].dst_vss) == 3

        # # Check that the VSes meant to be set active are in the AHG
        # assert VersionedName(frozenset("x"), 2) in new_ahg._variable_snapshots
        # assert VersionedName(frozenset("z"), 2) in new_ahg._variable_snapshots
