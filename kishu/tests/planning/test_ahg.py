from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import AHG, AHGUpdateInfo, CellExecution, VariableSnapshot, VersionedName


def test_add_cell_execution():
    ahg = AHG()
    vs1 = VariableSnapshot(frozenset("x"), 1)
    vs2 = VariableSnapshot(frozenset("y"), 1)

    newest_ce = ahg.add_cell_execution("", 1, [vs1], [vs2])

    cell_executions = ahg.get_cell_executions()

    # CE is stored in the graph correctly
    assert len(cell_executions) == 1

    # Newly create CE correctly set as adjacent CE of variable snapshots
    assert vs1.input_ces[0] == cell_executions[0]
    assert vs2.output_ce == cell_executions[0]
    assert newest_ce == cell_executions[0]


def test_from_db():
    ce1 = CellExecution(1)
    vs1 = VariableSnapshot(frozenset("x"), 1)
    vs2 = VariableSnapshot(frozenset("y"), 1)

    ce2 = CellExecution(2)
    vs3 = VariableSnapshot(frozenset("x"), 2)
    vs4 = VariableSnapshot(frozenset("y"), 2)

    vs_list = [vs1, vs2, vs3, vs4]
    ce_list = [ce1, ce2]
    vs_to_ce_edges = [
        (VersionedName(frozenset("x"), 1), 2),
        (VersionedName(frozenset("y"), 1), 2),
    ]
    ce_to_vs_edges = [
        (1, VersionedName(frozenset("x"), 1)),
        (1, VersionedName(frozenset("y"), 1)),
        (2, VersionedName(frozenset("x"), 2)),
        (2, VersionedName(frozenset("x"), 2)),
    ]

    ahg = AHG.from_db(vs_list, ce_list, vs_to_ce_edges, ce_to_vs_edges)

    variable_snapshots_dict = ahg.get_variable_snapshots_dict()
    cell_executions_dict = ahg.get_cell_executions_dict()

    assert variable_snapshots_dict == {
        VersionedName(frozenset("x"), 1): vs1,
        VersionedName(frozenset("y"), 1): vs2,
        VersionedName(frozenset("x"), 2): vs3,
        VersionedName(frozenset("y"), 2): vs4,
    }
    assert cell_executions_dict == {1: ce1, 2: ce2}

    # VS to CE edges set correctly
    assert vs1.input_ces == [ce2]
    assert vs1 in ce2.src_vss

    # CE to VS edges set correctly
    assert vs3.output_ce == ce2
    assert vs3 in ce2.dst_vss


def test_update_graph():
    ahg = AHG()

    # x and y are created
    update_result = ahg.update_graph(AHGUpdateInfo(version=1, cell_runtime_s=1.0, current_variables={"x", "y"}))
    assert update_result.accessed_vss == []
    assert set([vs.name for vs in update_result.output_vss]) == {frozenset("x"), frozenset("y")}
    assert update_result.newest_ce.cell_num == 0

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
    assert set([vs.name for vs in update_result.accessed_vss]) == {frozenset("x")}
    assert set([vs.name for vs in update_result.output_vss]) == {frozenset("x"), frozenset("y"), frozenset("z")}
    assert update_result.newest_ce.cell_num == 1

    variable_snapshots = ahg.get_variable_snapshots()
    active_variable_snapshots = ahg.get_active_variable_snapshots()
    cell_executions = ahg.get_cell_executions()

    # Check contents of AHG are correct
    assert len(variable_snapshots) == 5  # 2 versions of x + 2 versions of y + 1 version of z
    assert len(active_variable_snapshots) == 2
    assert len(cell_executions) == 2

    # x and z are active
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset("x"), frozenset("z")}

    # Check links between AHG contents are correct
    assert len(cell_executions[1].src_vss) == 1
    assert len(cell_executions[1].dst_vss) == 3


def test_augment_existing():
    ahg = AHG()

    # x and y are created
    _ = ahg.update_graph(AHGUpdateInfo(version=1, cell_runtime_s=1.0, current_variables={"x", "y"}))

    # Existing AHG is augmented
    namespace = Namespace({"a": 3, "b": 4, "In": ["print(x)\nprint(y)", "a=3\nb=4"]})
    update_result = ahg.augment_existing(namespace)

    assert update_result.newest_ce.cell_num == 1
    assert update_result.newest_ce.cell == "print(x)\nprint(y)\na=3\nb=4"  # Concatenated
    assert len(update_result.accessed_vss) == 0  # Accesses nothing
    assert len(update_result.output_vss) == 3  # x and y were deleted and {a, b} was created


def test_update_graph_with_connected_components():
    """
    Connected components:
    a---b---c  d---e  f
    """
    ahg = AHG()

    current_variables = {"a", "b", "c", "d", "e", "f"}
    linked_variable_pairs = [("a", "b"), ("b", "c"), ("d", "e")]
    _ = ahg.update_graph(
        AHGUpdateInfo(
            version=1, cell_runtime_s=1.0, current_variables=current_variables, linked_variable_pairs=linked_variable_pairs
        )
    )

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 3 variable snapshots
    assert len(active_variable_snapshots) == 3
    assert set(vs.name for vs in active_variable_snapshots) == {
        frozenset({"a", "b", "c"}),
        frozenset({"d", "e"}),
        frozenset("f"),
    }

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
    _ = ahg.update_graph(
        AHGUpdateInfo(
            version=1, cell_runtime_s=1.0, current_variables=current_variables, linked_variable_pairs=linked_variable_pairs
        )
    )

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 1 variable snapshot
    assert len(active_variable_snapshots) == 1

    # 1 connected component
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset({"a", "b", "c", "d", "e", "f"})}

    # 6 variables in total
    assert ahg.get_variable_names() == {"a", "b", "c", "d", "e", "f"}


def test_create_vs_split_connected_component():
    """
    Test modification detection for splitting comoponents:

    a---b

    split

    a   b
    """
    ahg = AHG()

    current_variables = {"a", "b"}
    linked_variable_pairs = [("a", "b")]

    # 'ab' is in 1 component.
    _ = ahg.update_graph(
        AHGUpdateInfo(
            version=1, cell_runtime_s=1.0, current_variables=current_variables, linked_variable_pairs=linked_variable_pairs
        )
    )

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 1 active variable snapshot
    assert len(active_variable_snapshots) == 1

    # 1 connected component
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset({"a", "b"})}

    # 'ab' is split into 2 components.
    _ = ahg.update_graph(
        AHGUpdateInfo(version=2, cell_runtime_s=1.0, current_variables=current_variables, modified_variables={"b"})
    )

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 2 active variable snapshots. Even though 'a' was not modified directly, we still count
    # it as modified as b was split from it.
    assert len(active_variable_snapshots) == 2

    # 2 connected components
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset("a"), frozenset("b")}


def test_create_vs_modify_connected_component():
    """
    Test modification detection for splitting comoponents:

    a---b   c

    split

    a   b---c
    """
    ahg = AHG()

    current_variables = {"a", "b", "c"}
    linked_variable_pairs = [("a", "b")]

    # 2 components: 'ab' and 'c'.
    _ = ahg.update_graph(
        AHGUpdateInfo(
            version=1, cell_runtime_s=1.0, current_variables=current_variables, linked_variable_pairs=linked_variable_pairs
        )
    )

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 2 active variable snapshots: ab and c.
    assert len(active_variable_snapshots) == 2

    # 2 connected components
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset({"a", "b"}), frozenset("c")}

    # 'ab' is split into 2 components.
    _ = ahg.update_graph(
        AHGUpdateInfo(
            version=2,
            cell_runtime_s=1.0,
            current_variables=current_variables,
            linked_variable_pairs=[("c", "b")],
            modified_variables={"b"},
        )
    )

    active_variable_snapshots = ahg.get_active_variable_snapshots()

    # 2 active variable snapshots.
    assert len(active_variable_snapshots) == 2

    # 2 connected components
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset({"c", "b"}), frozenset("a")}


def test_update_active_vses():
    ahg = AHG()

    # x and y are created
    _ = ahg.update_graph(AHGUpdateInfo(version=1, cell_runtime_s=1.0, current_variables={"x", "y"}))

    old_active_vses = ahg.clone_active_vses()

    # x is read and modified, z is created, y is deleted
    _ = ahg.update_graph(
        AHGUpdateInfo(
            version=2,
            cell_runtime_s=1.0,
            accessed_variables={"x"},
            current_variables={"x", "z"},
            modified_variables={"x"},
            deleted_variables={"y"},
        )
    )

    # State of active VSes after 2nd cell execution: x and z are active
    assert set(vs.name for vs in ahg.get_active_variable_snapshots()) == {frozenset("x"), frozenset("z")}

    # Replace state with that of after cell 1
    ahg.replace_active_vses(old_active_vses)

    # State of active VSes after 1st cell execution: x and z are active
    assert set(vs.name for vs in ahg.get_active_variable_snapshots()) == {frozenset("x"), frozenset("y")}
