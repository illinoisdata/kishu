from kishu.planning.ahg import AHG, VersionedName
from kishu.planning.optimizer import Optimizer


def test_optimizer(enable_slow_network_bandwidth):
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
    vs1 = ahg.create_variable_snapshot("x", deleted=False)
    vs2 = ahg.create_variable_snapshot("y", deleted=False)
    vs3 = ahg.create_variable_snapshot("z", deleted=True)
    vs1.size = 2
    vs2.size = 2
    active_vss = [vs1, vs2]

    # Cell executions
    ahg.add_cell_execution("", 3, [], [vs3])
    ahg.add_cell_execution("", 0.1, [vs3], [vs1])
    ahg.add_cell_execution("", 0.1, [vs3], [vs2])

    # Setup optimizer
    opt = Optimizer(ahg, active_vss, [])

    # Tests that the exact optimizer correctly escapes the local minimum by recomputing both x and y.
    vss_to_migrate, ces_to_recompute = opt.compute_plan()
    assert vss_to_migrate == set()
    assert ces_to_recompute == {0, 1, 2}


def test_optimizer_with_already_stored_variables(enable_slow_network_bandwidth):
    """
        Setup test graph.
        (cost:2) "x"  "y" (cost: 2)
             c3   |    |  c2
                 "z" "z"
                   "z"  (already stored)
                    | c1 (cost: 3)
                   []
    """
    ahg = AHG()

    # Variable snapshots
    vs1 = ahg.create_variable_snapshot("x", deleted=False)
    vs2 = ahg.create_variable_snapshot("y", deleted=False)
    vs3 = ahg.create_variable_snapshot("z", deleted=True)
    vs1.size = 2
    vs2.size = 2
    active_vss = [vs1, vs2]

    # Cell executions
    ahg.add_cell_execution("", 3, [], [vs3])
    ahg.add_cell_execution("", 0.1, [vs3], [vs1])
    ahg.add_cell_execution("", 0.1, [vs3], [vs2])

    # Setup optimizer
    opt = Optimizer(ahg, active_vss, [], already_stored_vss=[VersionedName(vs3.name, vs3.version)])

    # c1 is not recomputed as z is already stored.
    vss_to_migrate, ces_to_recompute = opt.compute_plan()
    assert vss_to_migrate == set()
    assert ces_to_recompute == {1, 2}
