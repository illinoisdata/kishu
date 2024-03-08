from kishu.planning.ahg import AHG, VariableSnapshot


def test_add_cell_execution():
    ahg = AHG()
    vs1 = VariableSnapshot(frozenset("x"), 1)
    vs2 = VariableSnapshot(frozenset("y"), 1)

    ahg.add_cell_execution("", 1, [vs1], [vs2])

    cell_executions = ahg.get_cell_executions()

    # CE is stored in the graph correctly
    assert len(cell_executions) == 1

    # Newly create CE correctly set as adjacent CE of variable snapshots
    assert vs1.input_ces[0] == cell_executions[0]
    assert vs2.output_ce == cell_executions[0]


def test_update_graph():
    ahg = AHG()

    # x and y are created
    ahg.update_graph("", 1, 1, {}, {"x", "y"}, [], {}, {})

    # x is read and modified, z is created, y is deleted
    ahg.update_graph("", 2, 1, {"x"}, {"x", "z"}, [], {"x"}, {"y"})

    variable_snapshots = ahg.get_variable_snapshots()
    active_variable_snapshots = ahg.get_active_variable_snapshots()
    cell_executions = ahg.get_cell_executions()

    # Check contents of AHG are correct
    assert len(variable_snapshots) == 5
    assert len(active_variable_snapshots) == 2
    assert len(cell_executions) == 2

    # x and z are active
    assert set(vs.name for vs in active_variable_snapshots) == set({frozenset("x"), frozenset("z")})

    # Check links between AHG contents are correct
    assert len(cell_executions[1].src_vss) == 1
    assert len(cell_executions[1].dst_vss) == 3


def test_update_graph_with_connected_components():
    """
        Connected components:
        a---b---c  d---e  f
    """
    ahg = AHG()

    current_variables = {"a", "b", "c", "d", "e", "f"}
    linked_variable_pairs = [("a", "b"), ("b", "c"), ("d", "e")]
    ahg.update_graph("", 2, 1, {}, current_variables, linked_variable_pairs, {}, {})

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 3 variable snapshots
    assert len(active_variable_snapshots) == 3
    assert set(vs.name for vs in active_variable_snapshots) == \
        {frozenset({"a", "b", "c"}), frozenset({"d", "e"}), frozenset("f")}

    # 6 variables in total
    assert ahg.get_variable_names() == {"a", "b", "c", "d", "e", "f"}


def test_create_vs_merge_connected_components():
    """
        Connected components:
           a--d
          /|  |
         / |  |
        b--c  e--f
    """
    ahg = AHG()

    current_variables = {"a", "b", "c", "d", "e", "f"}
    linked_variable_pairs = [("a", "b"), ("b", "c"), ("a", "c"), ("d", "e"), ("f", "e"), ("a", "f")]

    # components 'abc' and 'def' are merged.
    ahg.update_graph("", 2, 1, {}, current_variables, linked_variable_pairs, {}, {})

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 1 variable snapshot
    assert len(active_variable_snapshots) == 1

    # 1 connected component
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset({"a", "b", "c", "d", "e", "f"})}

    # 6 variables in total
    assert ahg.get_variable_names() == {"a", "b", "c", "d", "e", "f"}
