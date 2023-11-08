from kishu.planning.planner import CheckpointRestorePlanner


def test_checkpoint_restore_planner():
    """
        Test running a few cell updates.
    """
    user_ns = {}
    planner = CheckpointRestorePlanner(user_ns)

    # Pre run cell 1
    planner.pre_run_cell_update(set())

    # Post run cell 1
    user_ns["x"] = 1
    planner.post_run_cell_update("x = 1", {"x"}, 0.0, 1.0)

    # Pre run cell 2
    planner.pre_run_cell_update({"x"})

    # Post run cell 2
    user_ns["y"] = 2
    planner.post_run_cell_update("y = x + 1", {"x", "y"}, 1.0, 1.0)

    # Assert correct contents of AHG.
    assert planner._ahg.variable_snapshots.keys() == {"x", "y"}
    assert len(planner._ahg.variable_snapshots["x"]) == 1
    assert len(planner._ahg.variable_snapshots["y"]) == 1
    assert len(planner._ahg.cell_executions) == 2

    # Assert ID graphs are creaated.
    assert len(planner._id_graph_map.keys()) == 2

    # Create a checkpoint plan.
    restore_plan = planner.generate_restore_plan()

    # Assert that the restore plan has two actions in it.
    assert len(restore_plan.actions) == 2


def test_checkpoint_restore_planner_with_existing_items():
    """
        Test running a few cell updates.
    """
    user_ns = {"x": 1, "y": 2}
    planner = CheckpointRestorePlanner(user_ns)

    existing_vars = {"x", "y"}
    existing_cell_executions = ["x = 1", "y = 2"]

    planner.fill_ahg_with_existing_items(existing_vars, existing_cell_executions)

    # Assert correct contents of AHG. x and y are pessimistically assumed to be modified twice each.
    assert planner._ahg.variable_snapshots.keys() == {"x", "y"}
    assert len(planner._ahg.variable_snapshots["x"]) == 2
    assert len(planner._ahg.variable_snapshots["y"]) == 2
    assert len(planner._ahg.cell_executions) == 2

    # Pre run cell 3
    planner.pre_run_cell_update({"x", "y"})

    # Post run cell 3; x is incremented by 1.
    user_ns["x"] = 2
    planner.post_run_cell_update("x += 1", {"x", "y"}, 0.0, 1.0)

    # Assert correct contents of AHG is maintained after initializing the planner in a non-empty namespace.
    assert planner._ahg.variable_snapshots.keys() == {"x", "y"}
    assert len(planner._ahg.variable_snapshots["x"]) == 3
    assert len(planner._ahg.variable_snapshots["y"]) == 2
    assert len(planner._ahg.cell_executions) == 3
