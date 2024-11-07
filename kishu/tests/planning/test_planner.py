from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

import pytest

from kishu.jupyter.namespace import Namespace
from kishu.planning.plan import CheckpointPlan, RerunCellRestoreAction, RestorePlan, StepOrder
from kishu.planning.planner import ChangedVariables, CheckpointRestorePlanner
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.config import Config
from kishu.storage.path import KishuPath


@pytest.fixture()
def enable_always_migrate(tmp_kishu_path) -> Generator[type, None, None]:
    Config.set("OPTIMIZER", "always_migrate", True)
    yield Config
    Config.set("OPTIMIZER", "always_migrate", False)


class PlannerManager:
    """
    Class for automating pre and post-run-cell function calls in Planner.
    """

    def __init__(self, planner: CheckpointRestorePlanner):
        self.planner = planner

    def run_cell(
        self, ns_updates: Dict[str, Any], cell_code: str, ns_deletions: Set[str] = set(), cell_runtime: float = 1.0
    ) -> ChangedVariables:
        self.planner.pre_run_cell_update()

        # Update namespace.
        self.planner._user_ns.update(Namespace(ns_updates))

        # Delete variables from namespace.
        for var_name in ns_deletions:
            del self.planner._user_ns[var_name]

        # Return changed variables from post run cell update.
        return self.planner.post_run_cell_update(cell_code, cell_runtime)

    def checkpoint_session(
        self, database_path: Path, commit_id: str, parent_commit_ids: Optional[List[str]] = None
    ) -> Tuple[CheckpointPlan, RestorePlan]:
        checkpoint_plan, restore_plan = self.planner.generate_checkpoint_restore_plans(
            database_path, commit_id, parent_commit_ids
        )
        checkpoint_plan.run(self.planner._user_ns)
        return checkpoint_plan, restore_plan


def test_checkpoint_restore_planner(enable_always_migrate, nb_simple_path):
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

    # Assert ID graphs are created.
    assert len(planner.get_id_graph_map().keys()) == 2

    # Create checkpoint and restore plans.
    database_path = KishuPath.database_path(nb_simple_path)
    checkpoint_plan, restore_plan = planner.generate_checkpoint_restore_plans(database_path, "fake_commit_id")

    # Assert the plans have appropriate actions.
    assert len(checkpoint_plan.actions) == 1
    assert len(restore_plan.actions) == 2

    # Assert the restore plan has correct fields.
    assert restore_plan.actions[StepOrder(0, True)].fallback_recomputation == [
        RerunCellRestoreAction(StepOrder(0, False), "x = 1")
    ]


def test_checkpoint_restore_planner_with_existing_items(enable_always_migrate):
    """
    Test running a few cell updates.
    """
    user_ns = Namespace({"x": 1000, "y": 2000, "In": ["x = 1000", "y = 2000"]})

    planner = CheckpointRestorePlanner.from_existing(user_ns)

    variable_snapshots = planner.get_ahg().get_variable_snapshots()
    active_variable_snapshots = planner.get_ahg().get_active_variable_snapshots()
    cell_executions = planner.get_ahg().get_cell_executions()

    # Assert correct contents of AHG. x and y are pessimistically assumed to be modified twice each.
    assert len(variable_snapshots) == 2
    assert len(active_variable_snapshots) == 1
    assert active_variable_snapshots[0].name == frozenset({"x", "y"})
    assert len(cell_executions) == 2

    # Pre run cell 3
    planner.pre_run_cell_update()

    # Pre-running should fill in missing ID graph entries for x and y.
    assert len(planner.get_id_graph_map().keys()) == 2

    # Post run cell 3; x is incremented by 1.
    # If x and y are integers between 0-255, they will be detected as linked as they are stored in
    # fixed memory addresses.
    # TODO in a later PR: hardcode these cases as exceptions in ID graph to not consider as linking.
    user_ns["x"] = 2001
    planner.post_run_cell_update("x += 1", 1.0)

    variable_snapshots = planner.get_ahg().get_variable_snapshots()
    active_variable_snapshots = planner.get_ahg().get_active_variable_snapshots()
    cell_executions = planner.get_ahg().get_cell_executions()

    # Assert correct contents of AHG is maintained after initializing the planner in a non-empty namespace.
    assert len(variable_snapshots) == 4  # (x, y), (x, y), (x), (y)
    assert set(vs.name for vs in active_variable_snapshots) == {frozenset("x"), frozenset("y")}
    assert len(cell_executions) == 3


def test_post_run_cell_update_return(enable_always_migrate):
    planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

    # Run cell 1.
    changed_vars = planner_manager.run_cell({"x": 1}, "x = 1")

    assert changed_vars == ChangedVariables(
        created_vars={"x"}, modified_vars_value=set(), modified_vars_structure=set(), deleted_vars=set()
    )

    # Run cell 2.
    changed_vars = planner_manager.run_cell({"z": [1, 2], "y": 2, "x": 5}, "z = [1, 2]\ny = x + 1\nx = 5")

    assert changed_vars == ChangedVariables(
        created_vars={"y", "z"}, modified_vars_value={"x"}, modified_vars_structure={"x"}, deleted_vars=set()
    )

    # Run cell 3
    changed_vars = planner_manager.run_cell({"z": [1, 2]}, "z = [1, 2]\ndel x", ns_deletions={"x"})

    assert changed_vars == ChangedVariables(
        created_vars=set(),
        modified_vars_value=set(),
        modified_vars_structure={"z"},
        deleted_vars={"x"},
    )


class TestPlannerIncrementalCases:
    @pytest.fixture
    def db_path_name(self, nb_simple_path):
        return KishuPath.database_path(nb_simple_path)

    @pytest.fixture
    def kishu_checkpoint(self, db_path_name):
        """Fixture for initializing a KishuCheckpoint instance."""
        kishu_checkpoint = KishuCheckpoint(db_path_name)
        kishu_checkpoint.init_database()
        yield kishu_checkpoint
        kishu_checkpoint.drop_database()

    def test_checkpoint_restore_planner_incremental_store_simple(
        self, db_path_name, enable_incremental_store, enable_always_migrate, kishu_checkpoint
    ):
        """
        Test incremental store.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

        # Run cell 1.
        planner_manager.run_cell({"x": 1}, "x = 1")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1")

        # Run cell 2.
        planner_manager.run_cell({"y": 2}, "y = x + 1")

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that only 'y' is stored in the checkpoint plan - 'x' was stored in cell 1.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
        assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset("y")

    def test_checkpoint_restore_planner_incremental_store_skip_store(
        self, db_path_name, enable_incremental_store, enable_always_migrate, kishu_checkpoint
    ):
        """
        Test incremental store.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

        # Run cell 1.
        x = 1
        planner_manager.run_cell({"x": x, "y": [x], "z": [x]}, "x = 1\ny = [x]\nz = [x]")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1")

        # Run cell 2.
        planner_manager.run_cell({}, "print(x)")

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that nothing happens in the static cell 2.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 0

    def test_checkpoint_restore_planner_incremental_store_no_skip_store(
        self, db_path_name, enable_incremental_store, enable_always_migrate, kishu_checkpoint
    ):
        """
        Test incremental store.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({})))

        # Run cell 1.
        x = 1
        planner_manager.run_cell({"x": x, "y": [x], "z": [x]}, "x = 1\ny = [x]\nz = [x]")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1")

        # Run cell 2.
        planner_manager.run_cell({}, "del z", {"z"})

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that everything is stored again; {x, y} is a different VariableSnapshot vs. {x, y, z}.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
        assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset({"x", "y"})
