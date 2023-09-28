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
