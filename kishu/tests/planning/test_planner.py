import time
import pytest

from typing import Any, Dict, Generator, Set, Tuple

from kishu.jupyter.namespace import Namespace
from kishu.planning.planner import CheckpointRestorePlanner, ChangedVariables
from kishu.planning.plan import CheckpointPlan, RerunCellRestoreAction, RestorePlan, StepOrder
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.config import Config
from kishu.storage.path import KishuPath


@pytest.fixture()
def enable_always_migrate(tmp_kishu_path) -> Generator[type, None, None]:
    Config.set('OPTIMIZER', 'always_migrate', True)
    yield Config
    Config.set('OPTIMIZER', 'always_migrate', False)


class PlannerManager:
    """
        Class for automating pre and post-run-cell function calls in Planner.
    """
    def __init__(self, planner: CheckpointRestorePlanner):
        self.planner = planner

    def run_cell(
        self,
        ns_updates: Dict[str, Any],
        cell_code: str,
        ns_deletions: Set[str] = set(),
        cell_runtime: float = 1.0
    ) -> ChangedVariables:
        self.planner.pre_run_cell_update()

        # Update namespace.
        self.planner._user_ns.update(Namespace(ns_updates))

        # Delete variables from namespace.
        for var_name in ns_deletions:
            del self.planner._user_ns[var_name]

        # Return changed variables from post run cell update.
        return self.planner.post_run_cell_update(cell_code, time.time(), cell_runtime)

    def checkpoint_session(self, filename: str, commit_id: str) -> Tuple[CheckpointPlan, RestorePlan]:
        checkpoint_plan, restore_plan = self.planner.generate_checkpoint_restore_plans(filename, "1:1")
        checkpoint_plan.run(self.planner._user_ns)
        return checkpoint_plan, restore_plan


def test_checkpoint_restore_planner(enable_always_migrate):
    """
        Test running a few cell updates.
    """
    planner = CheckpointRestorePlanner(Namespace({}))
    planner_manager = PlannerManager(planner)

    # Run 2 cells.
    planner_manager.run_cell({"x": 1}, "x = 1")
    planner_manager.run_cell({"y": 2}, "y = x + 1")

    variable_snapshots = planner.get_ahg().get_variable_snapshots()
    cell_executions = planner.get_ahg().get_cell_executions()

    # Assert correct contents of AHG.
    assert variable_snapshots.keys() == {"x", "y"}
    assert len(variable_snapshots["x"]) == 1
    assert len(variable_snapshots["y"]) == 1
    assert len(cell_executions) == 2

    # Assert ID graphs are creaated.
    assert len(planner.get_id_graph_map().keys()) == 2

    # Create checkpoint and restore plans.
    checkpoint_plan, restore_plan = planner.generate_checkpoint_restore_plans("fake_path", "fake_commit_id")

    # Assert the plans have appropriate actions.
    assert len(checkpoint_plan.actions) == 1
    assert len(restore_plan.actions) == 2

    # Assert the restore plan has correct fields.
    assert restore_plan.actions[StepOrder(0, True)].fallback_recomputation == \
        [RerunCellRestoreAction(StepOrder(0, False), "x = 1")]


def test_checkpoint_restore_planner_with_existing_items(enable_always_migrate):
    """
        Test running a few cell updates.
    """
    user_ns = Namespace({"x": 1, "y": 2, "In": ["x = 1", "y = 2"]})

    planner = CheckpointRestorePlanner.from_existing(user_ns)

    variable_snapshots = planner.get_ahg().get_variable_snapshots()
    cell_executions = planner.get_ahg().get_cell_executions()

    # Assert correct contents of AHG. x and y are pessimistically assumed to be modified twice each.
    assert variable_snapshots.keys() == {"x", "y"}
    assert len(variable_snapshots["x"]) == 2
    assert len(variable_snapshots["y"]) == 2
    assert len(cell_executions) == 2

    # Pre run cell 3
    planner.pre_run_cell_update()

    # Pre-running should fill in missing ID graph entries for x and y.
    assert len(planner.get_id_graph_map().keys()) == 2

    # Post run cell 3; x is incremented by 1.
    user_ns["x"] = 2
    planner.post_run_cell_update("x += 1", 1.0, 1.0)

    # Assert correct contents of AHG is maintained after initializing the planner in a non-empty namespace.
    assert variable_snapshots.keys() == {"x", "y"}
    assert len(variable_snapshots["x"]) == 3
    assert len(variable_snapshots["y"]) == 2
    assert len(cell_executions) == 3


def test_post_run_cell_update_return(enable_always_migrate):
    planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

    # Run cell 1.
    changed_vars = planner_manager.run_cell({"x": 1}, "x = 1")

    assert changed_vars == ChangedVariables(
        created_vars={"x"},
        modified_vars_value=set(),
        modified_vars_structure=set(),
        deleted_vars=set()
    )

    # Run cell 2.
    changed_vars = planner_manager.run_cell({"z": [1, 2], "y": 2, "x": 5}, "z = [1, 2]\ny = x + 1\nx = 5")

    assert changed_vars == ChangedVariables(
        created_vars={"y", "z"},
        modified_vars_value={"x"},
        modified_vars_structure={"x"},
        deleted_vars=set()
    )

    # Run cell 3
    changed_vars = planner_manager.run_cell({"z": [1, 2]}, "z = [1, 2]\ndel x", ns_deletions={"x"})

    assert changed_vars == ChangedVariables(
        created_vars=set(),
        modified_vars_value=set(),
        modified_vars_structure={"z"},
        deleted_vars={"x"},
    )


def test_checkpoint_restore_planner_incremental_store_simple(enable_incremental_store, enable_always_migrate):
    """
        Test incremental store.
    """
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

    # Run cell 1.
    planner_manager.run_cell({"x": 1}, "x = 1")

    # Create and run checkpoint plan for cell 1.
    planner_manager.checkpoint_session(filename, "1:1")

    # Run cell 2.
    planner_manager.run_cell({"y": 2}, "y = x + 1")

    # Create and run checkpoint plan for cell 2.
    checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(filename, "1:2")

    # Assert that only 'y' is stored in the checkpoint plan - 'x' was stored in cell 1.
    assert len(checkpoint_plan_cell2.actions) == 1
    assert checkpoint_plan_cell2.actions[0].vs_connected_components.get_variable_names() == {"y"}


def test_checkpoint_restore_planner_incremental_store_not_subset(enable_incremental_store, enable_always_migrate):
    """
        Test incremental store.
    """
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

    # Run cell 1.
    x = 1
    planner_manager.run_cell({"x": x, "y": [x]}, "x = 1\ny = [x]")

    # Create and run checkpoint plan for cell 1.
    planner_manager.checkpoint_session(filename, "1:1")

    # Run cell 2.
    planner_manager.run_cell({"z": [x]}, "z = [x]")

    # Create and run checkpoint plan for cell 2.
    checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(filename, "1:2")

    # Assert that everything is stored again.
    # x and y are linked; since {x, y, z} is not a subset of the stored {x, y}, we need to store everything again.
    assert len(checkpoint_plan_cell2.actions) == 1
    assert checkpoint_plan_cell2.actions[0].vs_connected_components.get_variable_names() == {"x", "y", "z"}


def test_checkpoint_restore_planner_incremental_store_is_subset(enable_incremental_store, enable_always_migrate):
    """
        Test incremental store.
    """
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

    # Run cell 1.
    x = 1
    planner_manager.run_cell({"x": x, "y": [x], "z": [x]}, "x = 1\ny = [x]\nz = [x]")

    # Create and run checkpoint plan for cell 1.
    planner_manager.checkpoint_session(filename, "1:1")

    # Run cell 2.
    planner_manager.run_cell({}, "del z", {"z"})

    # Create and run checkpoint plan for cell 2.
    checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(filename, "1:2")

    # Assert that everything is stored again.
    # The connected component of 'x, y, z' is already stored, since 'x, y' is a subset, its storage is skipped.
    assert len(checkpoint_plan_cell2.actions) == 1
    assert checkpoint_plan_cell2.actions[0].vs_connected_components.get_variable_names() == set()
