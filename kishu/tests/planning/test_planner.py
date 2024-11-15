from pathlib import Path
from typing import Any, Dict, Generator, List, Set, Tuple

import pytest

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import AHGUpdateInfo
from kishu.planning.plan import CheckpointPlan, RerunCellRestoreAction, RestorePlan, StepOrder
from kishu.planning.planner import ChangedVariables, CheckpointRestorePlanner
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.commit import KishuCommit
from kishu.storage.commit_graph import KishuCommitGraph
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
        self, database_path: Path, commit_id: str, parent_commit_ids: List[str]
    ) -> Tuple[CheckpointPlan, RestorePlan]:
        checkpoint_plan, restore_plan = self.planner._generate_checkpoint_restore_plans(
            database_path, commit_id, parent_commit_ids
        )
        checkpoint_plan.run(self.planner._user_ns)
        return checkpoint_plan, restore_plan


class TestPlanner:
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

    @pytest.fixture
    def kishu_incremental_checkpoint(self, db_path_name):
        """Fixture for initializing a KishuCheckpoint instance with incremental CR."""
        kishu_incremental_checkpoint = KishuCheckpoint(db_path_name, incremental_cr=True)
        kishu_incremental_checkpoint.init_database()
        yield kishu_incremental_checkpoint
        kishu_incremental_checkpoint.drop_database()

    def test_checkpoint_restore_planner(self, enable_always_migrate, nb_simple_path):
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
        assert restore_plan.actions[StepOrder.new_load_variable(0)].fallback_recomputation == [
            RerunCellRestoreAction(StepOrder.new_rerun_cell(0), "x = 1")
        ]

    def test_checkpoint_restore_planner_with_existing_items(self, enable_always_migrate, nb_simple_path):
        """
        Test running a few cell updates.
        """
        user_ns = Namespace({"x": 1000, "y": 2000, "In": ["x = 1000", "y = 2000"]})

        planner = CheckpointRestorePlanner.from_existing(
            user_ns, KishuCommitGraph.new_var_graph(nb_simple_path), KishuCommit(nb_simple_path), False
        )

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

    def test_post_run_cell_update_return(self, enable_always_migrate):
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

    def test_checkpoint_restore_planner_incremental_store_simple(
        self, db_path_name, enable_always_migrate, kishu_incremental_checkpoint
    ):
        """
        Test incremental store.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({}), incremental_cr=True))

        # Run cell 1.
        planner_manager.run_cell({"x": 1}, "x = 1")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2.
        planner_manager.run_cell({"y": 2}, "y = x + 1")

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that only 'y' is stored in the checkpoint plan - 'x' was stored in cell 1.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
        assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset("y")

    def test_checkpoint_restore_planner_incremental_store_skip_store(
        self, db_path_name, enable_always_migrate, kishu_incremental_checkpoint
    ):
        """
        Test incremental store.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({}), incremental_cr=True))

        # Run cell 1.
        x = 1
        planner_manager.run_cell({"x": x, "y": [x], "z": [x]}, "x = 1\ny = [x]\nz = [x]")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2.
        planner_manager.run_cell({}, "print(x)")

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that nothing happens in the static cell 2.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 0

    def test_checkpoint_restore_planner_incremental_store_no_skip_store(
        self, db_path_name, enable_always_migrate, kishu_incremental_checkpoint
    ):
        """
        Test incremental store.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({}), incremental_cr=True))

        # Run cell 1.
        x = 1
        planner_manager.run_cell({"x": x, "y": [x], "z": [x]}, "x = 1\ny = [x]\nz = [x]")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2.
        planner_manager.run_cell({}, "del z", {"z"})

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that everything is stored again; {x, y} is a different VariableSnapshot vs. {x, y, z}.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
        assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset({"x", "y"})

    def test_checkpoint_restore_planner_incremental_restore_undo(
        self, db_path_name, enable_always_migrate, kishu_incremental_checkpoint
    ):
        """
        Test incremental restore with dynamically generated restore plan.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({}), incremental_cr=True))

        # Run cell 1.
        planner_manager.run_cell({"x": 1, "y": 2}, "x = 1\ny = 2")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Copy cell 1's AHG as lowest common ancestor AHG.
        lca_ahg = planner_manager.planner._ahg.clone()

        # Run cell 2. This modifies y and creates z.
        planner_manager.run_cell({"y": 3, "z": 4}, "y += 1\nz = 4")

        # Create and run checkpoint plan for cell 2.
        planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Generate the incremental restore plan for undoing to cell 1.
        restore_plan = planner_manager.planner._generate_incremental_restore_plan(db_path_name, lca_ahg, lca_ahg, ["1:1"])

        # The restore plan consists of moving X and loading Y.
        assert len(restore_plan.actions) == 2
        assert len(restore_plan.actions[StepOrder.new_incremental_load(0)].versioned_names) == 1
        assert restore_plan.actions[StepOrder.new_move_variable(0)].vars_to_move.keyset() == {"x"}

    def test_checkpoint_restore_planner_incremental_restore_branch(
        self, db_path_name, enable_always_migrate, kishu_incremental_checkpoint
    ):
        """
        Test incremental restore with dynamically generated restore plan.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({}), incremental_cr=True))

        # Run cell 1.
        planner_manager.run_cell({"x": 1, "y": 2}, "x = 1\ny = 2")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Copy cell 1's AHG as lowest common ancestor AHG.
        lca_ahg = planner_manager.planner._ahg.clone()

        # Run cell 2.
        planner_manager.run_cell({"y": 3, "z": 4}, "y += 1\nz = 4")

        # Create and run checkpoint plan for cell 2.
        planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        """
            Create the hypothetical target AHG in another branch with a diverged cell execution:
                 +- 1:2
            1:1 -+
                 +- target_ahg
        """
        cell_code = "x = y+x\nz=4"
        target_ahg = lca_ahg.clone()
        target_ahg.update_graph(
            AHGUpdateInfo(
                cell=cell_code,
                version=3,
                cell_runtime_s=1.0,
                accessed_variables={"x", "y"},
                current_variables={"x", "y", "z"},
                modified_variables={"x"},
            )
        )

        # Generate the incremental restore plan for checking out from 1:2 to the new branch.
        restore_plan = planner_manager.planner._generate_incremental_restore_plan(db_path_name, target_ahg, lca_ahg, ["1:1"])

        # The restore plan consists of moving X, loading Y, then rerunning cell 1
        # to modify x (to the version in cell 1) and recompute z.
        assert len(restore_plan.actions) == 3
        assert len(restore_plan.actions[StepOrder.new_incremental_load(0)].versioned_names) == 1
        assert restore_plan.actions[StepOrder.new_move_variable(0)].vars_to_move.keyset() == {"x"}
        assert restore_plan.actions[StepOrder.new_rerun_cell(1)].cell_code == cell_code

    def test_get_differing_vars_post_checkout(self, db_path_name, enable_always_migrate, kishu_incremental_checkpoint):
        """
        Tests the differing variables between pre and post-checkout are correctly identified.
        """
        planner_manager = PlannerManager(CheckpointRestorePlanner(Namespace({}), incremental_cr=True))

        # Run cell 1.
        planner_manager.run_cell({"x": 1, "y": 3}, "x = 1\ny = 3")

        # Copy cell 1's AHG as the state to undo to.
        target_ahg = planner_manager.planner._ahg.clone()

        # Run cell 2.
        planner_manager.run_cell({"x": 2, "y": 3}, "x += 1")

        assert planner_manager.planner._get_differing_vars_post_checkout(target_ahg) == {"x"}
