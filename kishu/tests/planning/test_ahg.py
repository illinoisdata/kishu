from kishu.planning.ahg import AHG, TimestampedName, VariableSnapshot, VsConnectedComponents


def test_create_variable_snapshot():
    """
        Test graph correctly handles timestamping of VSs with the same and different names.
    """
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", 1.0, False)
    vs2 = ahg.create_variable_snapshot("x", 2.0, False)
    vs3 = ahg.create_variable_snapshot("y", 3.0, False)

    # VSs are timestamped correcly
    assert vs1.timestamp == 1.0
    assert vs2.timestamp == 2.0
    assert vs3.timestamp == 3.0

    variable_snapshots = ahg.get_variable_snapshots()

    # VSs are stored in the graph correctly
    assert variable_snapshots.keys() == {"x", "y"}
    assert len(variable_snapshots["x"]) == 2
    assert len(variable_snapshots["y"]) == 1


def test_add_cell_execution():
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", 1.0, False)
    vs2 = ahg.create_variable_snapshot("y", 1.0, False)

    ahg.add_cell_execution("", 1, [vs1], [vs2])

    cell_executions = ahg.get_cell_executions()

    # CE is stored in the graph correctly
    assert len(cell_executions) == 1

    # Newly create CE correctly set as adjacent CE of variable snapshots
    assert vs1.input_ces[0] == cell_executions[0]
    assert vs2.output_ce == cell_executions[0]


def test_update_graph():
    ahg = AHG()
    vs1 = ahg.create_variable_snapshot("x", 1.0, False)
    _ = ahg.create_variable_snapshot("y", 1.0, False)

    # x is read and modified, z is created, y is deleted
    ahg.update_graph("", 2.0, 1, {"x"}, {"x", "z"}, {"y"})

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


def test_create_vs_connected_component_from_vses():
    """
        Connected components:
        a---b---c  d---e  f
    """
    vs_a = VariableSnapshot("a", 1.0)
    vs_b = VariableSnapshot("b", 1.0)
    vs_c = VariableSnapshot("c", 1.0)
    vs_d = VariableSnapshot("d", 1.0)
    vs_e = VariableSnapshot("e", 1.0)
    vs_f = VariableSnapshot("f", 1.0)

    vs_connected_components = VsConnectedComponents.create_from_vses(
        [vs_a, vs_b, vs_c, vs_d, vs_e, vs_f],
        [(vs_a, vs_b), (vs_b, vs_c), (vs_d, vs_e)]
    )

    # 3 connected components
    assert len(vs_connected_components.get_connected_components()) == 3
    assert {TimestampedName("a", 1.0),
            TimestampedName("b", 1.0),
            TimestampedName("c", 1.0)} in vs_connected_components.get_connected_components()
    assert {TimestampedName("d", 1.0),
            TimestampedName("e", 1.0)} in vs_connected_components.get_connected_components()
    assert {TimestampedName("f", 1.0)} in vs_connected_components.get_connected_components()

    # 6 VSes in total
    assert vs_connected_components.get_variable_names() == {"a", "b", "c", "d", "e", "f"}


def test_create_vs_merge_connected_components():
    """
        Connected components:
           a--d
          /|  |
         / |  |
        b--c  e--f
    """
    vs_a = VariableSnapshot("a", 1.0)
    vs_b = VariableSnapshot("b", 1.0)
    vs_c = VariableSnapshot("c", 1.0)
    vs_d = VariableSnapshot("d", 1.0)
    vs_e = VariableSnapshot("e", 1.0)
    vs_f = VariableSnapshot("f", 1.0)

    # components 'abc' and 'def' are merged.
    vs_connected_components = VsConnectedComponents.create_from_vses(
        [vs_a, vs_b, vs_c, vs_d, vs_e, vs_f],
        [(vs_a, vs_b), (vs_b, vs_c), (vs_a, vs_c), (vs_d, vs_e), (vs_f, vs_e), (vs_a, vs_f)]
    )

    # 1 connected component
    assert {
                TimestampedName("a", 1.0),
                TimestampedName("b", 1.0),
                TimestampedName("c", 1.0),
                TimestampedName("d", 1.0),
                TimestampedName("e", 1.0),
                TimestampedName("f", 1.0)
           } in vs_connected_components.get_connected_components()

    # 6 VSes in total
    assert vs_connected_components.get_variable_names() == {"a", "b", "c", "d", "e", "f"}


def test_is_subset_of_component():
    """
        Connected components:
        a---b---c  d---e  f
    """
    vs_connected_components = VsConnectedComponents.create_from_component_list(
        [[TimestampedName("a", 1.0), TimestampedName("b", 1.0), TimestampedName("c", 1.0)],
         [TimestampedName("d", 1.0), TimestampedName("e", 1.0)], [TimestampedName("f", 1.0)]]
    )

    assert vs_connected_components.contains_component(
        {TimestampedName("a", 1.0), TimestampedName("b", 1.0)})
    assert not vs_connected_components.contains_component(
        {TimestampedName("f", 1.0), TimestampedName("g", 1.0)})
