from typing import Generator

import pytest

from kishu.planning.ahg import AHG
from kishu.planning.optimizer import REALLY_FAST_BANDWIDTH_10GBPS, IncrementalLoadOptimizer, Optimizer
from kishu.storage.config import Config
from kishu.storage.disk_ahg import AHGUpdateResult, CellExecution, KishuDiskAHG, VariableSnapshot
from kishu.storage.path import KishuPath


@pytest.fixture()
def enable_slow_network_bandwidth(tmp_kishu_path) -> Generator[type, None, None]:
    Config.set("OPTIMIZER", "network_bandwidth", 1)
    yield Config
    Config.set("OPTIMIZER", "network_bandwidth", REALLY_FAST_BANDWIDTH_10GBPS)


@pytest.fixture()
def enable_always_migrate(tmp_kishu_path) -> Generator[type, None, None]:
    prev_value = Config.get("OPTIMIZER", "always_migrate", True)
    Config.set("OPTIMIZER", "always_migrate", True)
    yield Config
    Config.set("OPTIMIZER", "always_migrate", prev_value)


@pytest.fixture()
def disable_always_migrate(tmp_kishu_path) -> Generator[type, None, None]:
    prev_value = Config.get("OPTIMIZER", "always_migrate", True)
    Config.set("OPTIMIZER", "always_migrate", False)
    yield Config
    Config.set("OPTIMIZER", "always_migrate", prev_value)


class TestOptimizer:
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

    @pytest.fixture
    def test_ahg(self, kishu_disk_ahg) -> AHG:
        """
        Setup test graph.
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

        ahg = AHG(kishu_disk_ahg)
        return ahg

    def test_optimizer(self, test_ahg, disable_always_migrate, enable_slow_network_bandwidth):
        # Setup optimizer
        opt = Optimizer(test_ahg, test_ahg.get_active_variable_snapshots("1:3"))

        # Tests that the exact optimizer correctly escapes the local minimum by recomputing both y and z.
        vss_to_migrate, ces_to_recompute = opt.compute_plan()
        assert vss_to_migrate == set()
        assert set(ce.cell_num for ce in ces_to_recompute) == {1, 2, 3}

    def test_optimizer_always_migrate(self, test_ahg, enable_always_migrate, enable_slow_network_bandwidth):
        # Setup optimizer
        opt = Optimizer(test_ahg, test_ahg.get_active_variable_snapshots("1:3"))

        # Both y and z are migrated due to the flag.
        vss_to_migrate, ces_to_recompute = opt.compute_plan()
        assert set(vs.name for vs in vss_to_migrate) == {frozenset({"y"}), frozenset({"z"})}
        assert ces_to_recompute == set()

    def test_optimizer_with_already_stored_variables(
        self, test_ahg, enable_slow_network_bandwidth, disable_always_migrate, enable_incremental_store
    ):
        # Setup optimizer
        opt = Optimizer(
            test_ahg,
            test_ahg.get_active_variable_snapshots("1:3"),
            already_stored_vss=test_ahg.get_active_variable_snapshots("1:1"),  # x was stored prior to being deleted
        )

        # c1 is not recomputed as x is already stored.
        vss_to_migrate, ces_to_recompute = opt.compute_plan()
        assert vss_to_migrate == set()
        assert set(ce.cell_num for ce in ces_to_recompute) == {2, 3}

    def test_incremental_load_optimizer_moves(self, test_ahg, enable_slow_network_bandwidth, enable_incremental_store):
        # Problem setting: we want to restore to a state with VSes y and z, which are both present in the current namespace
        target_active_vss = test_ahg.get_active_variable_snapshots("1:3")  # y and z
        useful_active_vss = test_ahg.get_active_variable_snapshots("1:3")  # y and z
        useful_stored_vss = {}

        # The plan is to move VSes y and z from the old namespace to the new namespace (and do nothing else).
        opt_result = IncrementalLoadOptimizer(test_ahg, target_active_vss, useful_active_vss, useful_stored_vss).compute_plan()
        assert opt_result.vss_to_move == set(test_ahg.get_active_variable_snapshots("1:3"))  # y and z
        assert opt_result.vss_to_load == set()
        assert opt_result.ces_to_rerun == set()

    def test_incremental_load_optimizer_rerun(self, test_ahg, enable_slow_network_bandwidth, enable_incremental_store):
        # Problem setting: we want to restore to a state with VSes y and z from a clean namespace and database.
        target_active_vss = test_ahg.get_active_variable_snapshots("1:3")  # y and z
        useful_active_vss = {}
        useful_stored_vss = {}

        # The plan is to rerun all cells.
        opt_result = IncrementalLoadOptimizer(test_ahg, target_active_vss, useful_active_vss, useful_stored_vss).compute_plan()
        assert set(opt_result.vss_to_move) == set()
        assert set(opt_result.vss_to_load) == set()
        assert set(ce.cell_num for ce in opt_result.ces_to_rerun) == {1, 2, 3}

    def test_incremental_load_optimizer_mixed(self, test_ahg, enable_slow_network_bandwidth, enable_incremental_store):
        # Problem setting: y can be moved while z is to be recomputed.
        vs_x = next(iter(test_ahg.get_active_variable_snapshots("1:1")))
        vs_y = next(
            iter(test_ahg.get_active_variable_snapshots("1:2").difference(test_ahg.get_active_variable_snapshots("1:1")))
        )

        target_active_vss = test_ahg.get_active_variable_snapshots("1:3")  # y and z
        useful_active_vss = {vs_y}
        useful_stored_vss = {vs_x}  # x

        # The plan is to load x, move y, and rerun cell 2 (to recompute z).
        opt_result = IncrementalLoadOptimizer(test_ahg, target_active_vss, useful_active_vss, useful_stored_vss).compute_plan()
        assert set(opt_result.vss_to_move) == {vs_y}
        assert set(opt_result.vss_to_load) == {vs_x}  # x
        assert set(ce.cell_num for ce in opt_result.ces_to_rerun) == {3}

        # Assert the correct fallback recomputations for VS x exists (to rerun cell 1).
        assert len(opt_result.fallback_recomputation) == 1
        assert set(ce.cell_num for ce in opt_result.fallback_recomputation[vs_x]) == {1}
