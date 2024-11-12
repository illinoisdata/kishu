from typing import Generator

import pytest

from kishu.planning.ahg import AHG, VariableSnapshot, VersionedName
from kishu.planning.optimizer import IncrementalLoadOptimizer, Optimizer, REALLY_FAST_BANDWIDTH_10GBPS
from kishu.storage.config import Config


@pytest.fixture()
def enable_slow_network_bandwidth(tmp_kishu_path) -> Generator[type, None, None]:
    Config.set("OPTIMIZER", "network_bandwidth", 1)
    yield Config
    Config.set("OPTIMIZER", "network_bandwidth", REALLY_FAST_BANDWIDTH_10GBPS)


@pytest.fixture
def test_ahg() -> AHG:
    """
    Setup test graph.
    (cost:2) "x"  "y" (cost: 2)
         c3   |    |  c2
             "z" "z"
               "z"
                | c1 (cost: 3)
               []
    """
    ahg = AHG()

    # Variable snapshots
    vs1 = VariableSnapshot(frozenset("x"), 3, deleted=False)
    vs2 = VariableSnapshot(frozenset("y"), 2, deleted=False)
    vs3 = VariableSnapshot(frozenset("z"), 1, deleted=True)
    vs1.size = 2
    vs2.size = 2
    ahg._active_variable_snapshots[frozenset("x")] = vs1
    ahg._active_variable_snapshots[frozenset("y")] = vs2

    # Cell executions
    ahg.add_cell_execution("", 3, [], [vs3])
    ahg.add_cell_execution("", 0.1, [vs3], [vs1])
    ahg.add_cell_execution("", 0.1, [vs3], [vs2])

    return ahg


def test_optimizer(test_ahg, enable_slow_network_bandwidth):
    # Setup optimizer
    opt = Optimizer(test_ahg, test_ahg.get_active_variable_snapshots())

    # Tests that the exact optimizer correctly escapes the local minimum by recomputing both x and y.
    vss_to_migrate, ces_to_recompute = opt.compute_plan()
    assert vss_to_migrate == set()
    assert ces_to_recompute == {0, 1, 2}


def test_optimizer_with_already_stored_variables(test_ahg, enable_slow_network_bandwidth, enable_incremental_store):
    # Setup optimizer
    opt = Optimizer(
        test_ahg, test_ahg.get_active_variable_snapshots(), already_stored_vss={VersionedName(frozenset("z"), 1): 1}
    )

    # c1 is not recomputed as z is already stored.
    vss_to_migrate, ces_to_recompute = opt.compute_plan()
    assert vss_to_migrate == set()
    assert ces_to_recompute == {1, 2}


def test_incremental_load_optimizer_moves(test_ahg, enable_slow_network_bandwidth, enable_incremental_store):
    # Problem setting: we want to restore to a state with VSes x and y, which are both present in the current namespace
    target_active_vss = test_ahg.get_active_variable_snapshots()
    useful_active_vss = {VersionedName(frozenset("x"), 3), VersionedName(frozenset("y"), 2)}
    useful_stored_vss = {}

    # The plan is to move VSes x and y from the old namespace to the new namespace (and do nothing else).
    opt_result = IncrementalLoadOptimizer(target_active_vss, useful_active_vss, useful_stored_vss).compute_plan()
    assert set(opt_result.vss_to_move.keys()) == {VersionedName(frozenset("x"), 3), VersionedName(frozenset("y"), 2)}
    assert set(opt_result.vss_to_load.keys()) == set()
    assert opt_result.ces_to_rerun == set()


def test_incremental_load_optimizer_rerun(test_ahg, enable_slow_network_bandwidth, enable_incremental_store):
    # Problem setting: we want to restore to a state with VSes x and y from a clean namespace and database.
    target_active_vss = test_ahg.get_active_variable_snapshots()
    useful_active_vss = {}
    useful_stored_vss = {}

    # The plan is to rerun all cells.
    opt_result = IncrementalLoadOptimizer(target_active_vss, useful_active_vss, useful_stored_vss).compute_plan()
    assert set(opt_result.vss_to_move.keys()) == set()
    assert set(opt_result.vss_to_load.keys()) == set()
    assert opt_result.ces_to_rerun == {0, 1, 2}


def test_incremental_load_optimizer_mixed(test_ahg, enable_slow_network_bandwidth, enable_incremental_store):
    # Problem setting: x can be moved while z is to be
    target_active_vss = test_ahg.get_active_variable_snapshots()
    useful_active_vss = {VersionedName(frozenset("x"), 3)}
    useful_stored_vss = {VersionedName(frozenset("z"), 1)}

    # The plan is to load z, move x, and rerun cell 2 (to recompute y).
    opt_result = IncrementalLoadOptimizer(target_active_vss, useful_active_vss, useful_stored_vss).compute_plan()
    assert set(opt_result.vss_to_move.keys()) == {VersionedName(frozenset("x"), 3)}
    assert set(opt_result.vss_to_load.keys()) == {VersionedName(frozenset("z"), 1)}
    assert opt_result.ces_to_rerun == {2}

    # Assert the correct fallback recomputations exist.
    assert len(opt_result.fallback_recomputation) == 1
    assert opt_result.fallback_recomputation[VersionedName(frozenset("z"), 1)] == {0}
