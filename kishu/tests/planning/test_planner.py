import copy
import pytest

from typing import Any, Dict, Generator, List, Optional, Set, Tuple

from kishu.jupyter.namespace import Namespace
from kishu.planning.planner import CheckpointRestorePlanner, ChangedVariables
from kishu.planning.plan import CheckpointPlan, RerunCellRestoreAction, RestoreActionOrder, RestorePlan, StepOrder
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
        return self.planner.post_run_cell_update(cell_code, cell_runtime)

    def checkpoint_session(self, filename: str, commit_id: str, parent_commit_ids: Optional[List[str]]=None) -> Tuple[CheckpointPlan, RestorePlan]:
        checkpoint_plan, restore_plan = self.planner.generate_checkpoint_restore_plans(filename, commit_id, parent_commit_ids)
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
    active_variable_snapshots = planner.get_ahg().get_active_variable_snapshots()
    cell_executions = planner.get_ahg().get_cell_executions()

    # Assert correct contents of AHG.
    assert len(variable_snapshots) == 2
    assert len(active_variable_snapshots) == 2
    assert len(cell_executions) == 2

    # Assert ID graphs are creaated.
    assert len(planner.get_id_graph_map().keys()) == 2

    # Create checkpoint and restore plans.
    checkpoint_plan, restore_plan = planner.generate_checkpoint_restore_plans("fake_path", "fake_commit_id")

    # Assert the plans have appropriate actions.
    assert len(checkpoint_plan.actions) == 1
    assert len(restore_plan.actions) == 2

    # Assert the restore plan has correct fields.
    assert restore_plan.actions[StepOrder(0, RestoreActionOrder.LOAD_VARIABLE)].fallback_recomputation == \
        [RerunCellRestoreAction(StepOrder(0, RestoreActionOrder.RERUN_CELL), "x = 1")]


def test_checkpoint_restore_planner_with_existing_items(enable_always_migrate):
    """
        Test running a few cell updates.
    """
    user_ns = Namespace({"x": 1000, "y": 2000, "In": ["x = 1000", "y = 2000"]})

    planner = CheckpointRestorePlanner.from_existing(user_ns)

    variable_snapshots = planner.get_ahg().get_variable_snapshots()
    active_variable_snapshots = planner.get_ahg().get_active_variable_snapshots()
    cell_executions = planner.get_ahg().get_cell_executions()

    # Assert correct contents of AHG. x and y are pessimistically assumed to linked and modified twice.
    assert len(variable_snapshots) == 2
    assert len(active_variable_snapshots) == 1
    assert len(cell_executions) == 2

    # Pre run cell 3
    planner.pre_run_cell_update()

    # Pre-running should fill in missing ID graph entries for x and y.
    assert len(planner.get_id_graph_map().keys()) == 2

    # Post run cell 3; x is incremented by 1.
    user_ns["x"] = 2
    planner.post_run_cell_update("x += 1", 1.0)

    variable_snapshots = planner.get_ahg().get_variable_snapshots()
    active_variable_snapshots = planner.get_ahg().get_active_variable_snapshots()
    cell_executions = planner.get_ahg().get_cell_executions()

    # Assert correct contents of AHG is maintained after initializing the planner in a non-empty namespace.
    # X and y are discovered to be unlinked.
    assert len(variable_snapshots) == 4
    assert len(active_variable_snapshots) == 2
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
    planner_manager.checkpoint_session(filename, "1:1", [])

    # Run cell 2.
    planner_manager.run_cell({"y": 2}, "y = x + 1")

    # Create and run checkpoint plan for cell 2.
    checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(filename, "1:2", ["1:1"])

    # Assert that only 'y' is stored in the checkpoint plan - 'x' was stored in cell 1.
    assert len(checkpoint_plan_cell2.actions) == 1
    assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
    assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset("y")


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
    planner_manager.checkpoint_session(filename, "1:1", [])

    # Run cell 2.
    planner_manager.run_cell({"z": [x]}, "z = [x]")

    # Create and run checkpoint plan for cell 2.
    checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(filename, "1:2", ["1:1"])

    # Assert that everything is stored again.
    # x and y are linked; since {x, y, z} is not a subset of the stored {x, y}, we need to store everything again.
    assert len(checkpoint_plan_cell2.actions) == 1
    assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
    assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset({"x", "y", "z"})


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
    planner_manager.checkpoint_session(filename, "1:1", [])

    # Run cell 2.
    planner_manager.run_cell({}, "del z", {"z"})

    # Create and run checkpoint plan for cell 2.
    checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(filename, "1:2", ["1:1"])

    # Assert that everything is stored again.
    # The connected component of 'x, y, z' is already stored, since 'x, y' is a subset, its storage is skipped.
    assert len(checkpoint_plan_cell2.actions) == 1
    assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
    assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset({"x", "y"})


def test_checkpoint_restore_planner_incremental_restore(enable_incremental_store, enable_always_migrate):
    """
        Test incremental restore with dynamically generated restore plan.
    """
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

    # Run cell 1.
    planner_manager.run_cell({"x": 1, "y": 2}, "x = 1\ny = 2")

    # Create and run checkpoint plan for cell 1.
    planner_manager.checkpoint_session(filename, "1:1", [])

    # Copy cell 1's AHG as lowest common ancestor AHG.
    lca_ahg = copy.deepcopy(planner_manager.planner._ahg)

    # Run cell 2.
    planner_manager.run_cell({"y": 3, "z": 4}, "y += 1\nz = 4")

    # Create and run checkpoint plan for cell 2.
    planner_manager.checkpoint_session(filename, "1:2", ["1:1"])

    # Generate the incremental restore plan for restoring to cell 1.
    restore_plan = planner_manager.planner.generate_incremental_restore_plan(lca_ahg, lca_ahg, filename, ["1:1"])

    # The restore plan consists of moving X and loading Y.
    assert len(restore_plan.actions) == 2
    assert len(restore_plan.actions[StepOrder(0, RestoreActionOrder.INCREMENTAL_LOAD)].versioned_names) == 1
    assert restore_plan.actions[StepOrder(0, RestoreActionOrder.MOVE_VARIABLE)].vars_to_move.keyset() == {"x"}
