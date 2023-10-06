from kishu.planning.ahg import AHG


def test_create_variable_snapshot():
    """
        Test graph correctly handles versioning of VSs with the same and different names.
    """
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", False)
    vs2 = ahg.create_variable_snapshot("x", False)
    vs3 = ahg.create_variable_snapshot("y", False)

    # VSs are versioned correcly
    assert vs1.version == 0
    assert vs2.version == 1  # vs2 is second VS for variable x
    assert vs3.version == 0

    # VSs are stored in the graph correctly
    assert ahg.variable_snapshots.keys() == {"x", "y"}
    assert len(ahg.variable_snapshots["x"]) == 2
    assert len(ahg.variable_snapshots["y"]) == 1


def test_add_cell_execution():
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", False)
    vs2 = ahg.create_variable_snapshot("y", False)

    ahg.add_cell_execution("", 1, 1, [vs1], [vs2])

    # CE is stored in the graph correctly
    assert len(ahg.cell_executions) == 1

    # Newly create CE correctly set as adjacent CE of variable snapshots
    assert vs1.input_ces[0] == ahg.cell_executions[0]
    assert vs2.output_ce == ahg.cell_executions[0]


def test_update_graph():
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", False)
    _ = ahg.create_variable_snapshot("y", False)

    # x is read and modified, z is created, y is deleted
    ahg.update_graph("", 1, 1, {"x"}, {"x", "z"}, {"y"})

    # Check contents of AHG are correct
    assert len(ahg.cell_executions) == 1
    assert ahg.variable_snapshots.keys() == {"x", "y", "z"}
    assert len(ahg.variable_snapshots["x"]) == 2
    assert len(ahg.variable_snapshots["y"]) == 2
    assert len(ahg.variable_snapshots["z"]) == 1

    # Check links between AHG contents are correct
    assert vs1.input_ces[0] == ahg.cell_executions[0]
    assert len(ahg.cell_executions[0].src_vss) == 1
    assert len(ahg.cell_executions[0].dst_vss) == 3
