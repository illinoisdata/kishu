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

    variable_snapshots = ahg.get_variable_snapshots()

    # VSs are stored in the graph correctly
    assert variable_snapshots.keys() == {"x", "y"}
    assert len(variable_snapshots["x"]) == 2
    assert len(variable_snapshots["y"]) == 1


def test_add_cell_execution():
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", False)
    vs2 = ahg.create_variable_snapshot("y", False)

    ahg.add_cell_execution("", 1, 1, [vs1], [vs2])

    cell_executions = ahg.get_cell_executions()

    # CE is stored in the graph correctly
    assert len(cell_executions) == 1

    # Newly create CE correctly set as adjacent CE of variable snapshots
    assert vs1.input_ces[0] == cell_executions[0]
    assert vs2.output_ce == cell_executions[0]


def test_update_graph():
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", False)
    _ = ahg.create_variable_snapshot("y", False)

    # x is read and modified, z is created, y is deleted
    ahg.update_graph("", 1, 1, {"x"}, {"x", "z"}, {"y"})

    variable_snapshots = ahg.get_variable_snapshots()
    cell_executions = ahg.get_cell_executions()

    # Check contents of AHG are correct
    assert len(cell_executions) == 1
    assert variable_snapshots.keys() == {"x", "y", "z"}
    assert len(variable_snapshots["x"]) == 2
    assert len(variable_snapshots["y"]) == 2
    assert len(variable_snapshots["z"]) == 1

    # Check links between AHG contents are correct
    assert vs1.input_ces[0] == cell_executions[0]
    assert len(cell_executions[0].src_vss) == 1
    assert len(cell_executions[0].dst_vss) == 3
