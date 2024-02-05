from kishu.planning.ahg import AHG
from kishu.planning.optimizer import Optimizer


def test_optimizer():
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
    vs1 = ahg.create_variable_snapshot("x", False)
    vs2 = ahg.create_variable_snapshot("y", False)
    vs3 = ahg.create_variable_snapshot("z", True)
    vs1.size = 2
    vs2.size = 2
    active_vss = [vs1, vs2]

    # Cell executions
    ahg.add_cell_execution("", 3, [], [vs3])
    ahg.add_cell_execution("", 0.1, [vs3], [vs1])
    ahg.add_cell_execution("", 0.1, [vs3], [vs2])

    # Setup optimizer
    opt = Optimizer(ahg, active_vss, [], migration_speed_bps=1)

    # Tests that the exact optimizer correctly escapes the local minimum by recomputing both x and y.
    vss_to_migrate, ces_to_recompute = opt.compute_plan()
    assert vss_to_migrate == set()
    assert ces_to_recompute == {0, 1, 2}
