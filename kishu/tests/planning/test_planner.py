from pathlib import Path
from typing import Any, Dict, Generator, List, Set, Tuple

import pytest

from kishu.jupyter.namespace import Namespace
from kishu.planning.plan import CheckpointPlan, RerunCellRestoreAction, RestorePlan, StepOrder
from kishu.planning.planner import ChangedVariables, CheckpointRestorePlanner
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.commit_graph import CommitId, KishuCommitGraph
from kishu.storage.config import Config
from kishu.storage.disk_ahg import KishuDiskAHG
from kishu.storage.path import KishuPath


@pytest.fixture()
def enable_always_migrate(tmp_kishu_path) -> Generator[type, None, None]:
    prev_value = Config.get("OPTIMIZER", "always_migrate", True)
    Config.set("OPTIMIZER", "always_migrate", True)
    yield Config
    Config.set("OPTIMIZER", "always_migrate", prev_value)


class PlannerManager:
    """
    Class for automating pre and post-run-cell function calls in Planner.
    """

    def __init__(self, planner: CheckpointRestorePlanner):
        self.planner = planner

    def run_cell(
        self,
        commit_id: CommitId,
        ns_accesses: Set[str],
        ns_updates: Dict[str, Any],
        cell_code: str,
        ns_deletions: Set[str] = set(),
        cell_runtime: float = 1.0,
    ) -> ChangedVariables:
        self.planner.pre_run_cell_update()

        # Update namespace. KV-pairs are manually set as update() does not trigger __setitem__.
        for k, v in ns_updates.items():
            self.planner._user_ns[k] = v

        # Mock access variables.
        for var in ns_accesses:
            _ = self.planner._user_ns[var]

        # Delete variables from namespace.
        for var_name in ns_deletions:
            del self.planner._user_ns[var_name]

        # Return changed variables from post run cell update.
        res = self.planner.post_run_cell_update(commit_id, cell_code, cell_runtime)

        # step the contained kishu graph.
        self.planner._kishu_graph.step(commit_id)

        return res

    def checkpoint_session(
        self, database_path: Path, commit_id: CommitId, parent_commit_ids: List[str]
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
    def graph_name(self):
        return "test_graph"

    @pytest.fixture
    def kishu_disk_ahg(self, db_path_name):
        """Fixture for initializing a KishuBranch instance."""
        kishu_disk_ahg = KishuDiskAHG(db_path_name)
        kishu_disk_ahg.init_database()
        yield kishu_disk_ahg
        kishu_disk_ahg.drop_database()

    @pytest.fixture
    def kishu_graph(self, db_path_name, graph_name):
        """Fixture for initializing a KishuBranch instance."""
        kishu_graph = KishuCommitGraph(db_path_name, graph_name)
        kishu_graph.init_database()
        yield kishu_graph
        kishu_graph.drop_database()

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

    def test_checkpoint_restore_planner(self, nb_simple_path, enable_always_migrate, kishu_disk_ahg, kishu_graph):
        """
        Test running a few cell updates.
        """
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}))
        planner_manager = PlannerManager(planner)

        # Run 2 cells.
        planner_manager.run_cell("1:1", {}, {"x": 1}, "x = 1")
        planner_manager.run_cell("1:2", {"x"}, {"y": 2}, "y = x + 1")

        # Assert correct contents of AHG.
        assert len(planner.get_ahg().get_all_variable_snapshots()) == 2
        assert len(planner.get_ahg().get_all_cell_executions()) == 2
        assert len(planner.get_ahg().get_active_variable_snapshots("1:2")) == 2  # x, y

        # Assert ID graphs are created.
        assert len(planner.get_id_graph_map().keys()) == 2

        # Create checkpoint and restore plans.
        database_path = KishuPath.database_path(nb_simple_path)
        checkpoint_plan, restore_plan = planner.generate_checkpoint_restore_plans(database_path, "1:2")

        # Assert the plans have appropriate actions.
        assert len(checkpoint_plan.actions) == 1
        assert len(restore_plan.actions) == 2

        # Assert the restore plan has correct fields.
        version = min([ce.cell_num for ce in planner.get_ahg().get_all_cell_executions()])  # Get timestamp from stored CE
        assert restore_plan.actions[StepOrder.new_load_variable(version)].fallback_recomputation == [
            RerunCellRestoreAction(StepOrder.new_rerun_cell(version), "x = 1\n")
        ]

    def test_checkpoint_restore_planner_with_existing_items(
        self, nb_simple_path, enable_always_migrate, kishu_disk_ahg, kishu_graph
    ):
        """
        Test running a few cell updates.
        """
        # Namespace contains untracked cells 1 and 2.
        user_ns = Namespace({"x": 1, "y": 2, "In": ["%%time\nx = 1", "%%time\ny = 2"]})

        planner = CheckpointRestorePlanner.from_existing(user_ns, kishu_disk_ahg, kishu_graph, incremental_cr=False)
        planner_manager = PlannerManager(planner)

        # Nothing has been stored yet.
        assert len(planner.get_ahg().get_all_variable_snapshots()) == 0
        assert len(planner.get_ahg().get_active_variable_snapshots("1:2")) == 0
        assert len(planner.get_ahg().get_all_cell_executions()) == 0

        # Run cell 3; x is incremented by 1.
        planner_manager.run_cell("1:3", {"x"}, {"x": 2}, "%%time\nx += 1")

        # Assert correct contents of AHG is maintained after initializing the planner in a non-empty namespace.
        assert len(planner.get_ahg().get_all_variable_snapshots()) == 2
        assert len(planner.get_ahg().get_all_cell_executions()) == 1  # 2 existing cells in In concatenated onto x += 1
        assert set(vs.name for vs in planner.get_ahg().get_active_variable_snapshots("1:3")) == {
            frozenset("x"),
            frozenset("y"),
        }

    def test_post_run_cell_update_return(self, enable_always_migrate, kishu_disk_ahg, kishu_graph):
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}))
        planner_manager = PlannerManager(planner)

        # Run cell 1.
        changed_vars = planner_manager.run_cell("1:1", {}, {"x": 1}, "x = 1")

        assert changed_vars == ChangedVariables(
            created_vars={"x"}, modified_vars_value=set(), modified_vars_structure=set(), deleted_vars=set()
        )

        # Run cell 2.
        changed_vars = planner_manager.run_cell("1:2", {"x"}, {"z": [1, 2], "y": 2, "x": 5}, "z = [1, 2]\ny = x + 1\nx = 5")

        assert changed_vars == ChangedVariables(
            created_vars={"y", "z"}, modified_vars_value={"x"}, modified_vars_structure={"x"}, deleted_vars=set()
        )

        # Run cell 3
        changed_vars = planner_manager.run_cell("1:3", {}, {"z": [1, 2]}, "z = [1, 2]\ndel x", ns_deletions={"x"})

        assert changed_vars == ChangedVariables(
            created_vars=set(),
            modified_vars_value=set(),
            modified_vars_structure=set(),
            deleted_vars={"x"},
        )

    def test_checkpoint_restore_planner_incremental_store_simple(
        self, db_path_name, enable_always_migrate, kishu_disk_ahg, kishu_graph, kishu_incremental_checkpoint
    ):
        """
        Test incremental store.
        """
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}), incremental_cr=True)
        planner_manager = PlannerManager(planner)

        # Run cell 1.
        planner_manager.run_cell("1:1", {}, {"x": 1}, "x = 1")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2.
        planner_manager.run_cell("1:2", {"x"}, {"y": 2}, "y = x + 1")

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that only 'y' is stored in the checkpoint plan - 'x' was stored in cell 1.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
        assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset("y")

    def test_checkpoint_restore_planner_incremental_store_skip_store(
        self, db_path_name, enable_always_migrate, kishu_disk_ahg, kishu_graph, kishu_incremental_checkpoint
    ):
        """
        Test incremental store.
        """
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}), incremental_cr=True)
        planner_manager = PlannerManager(planner)

        # Run cell 1.
        x = 1
        planner_manager.run_cell("1:1", {"x"}, {"x": x, "y": [x], "z": [x]}, "x = 1\ny = [x]\nz = [x]")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2.
        planner_manager.run_cell("1:2", {"x"}, {}, "print(x)")

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that nothing happens in the static cell 2.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 0

    def test_checkpoint_restore_planner_incremental_store_no_skip_store(
        self,
        db_path_name,
        enable_incremental_store,
        enable_always_migrate,
        kishu_disk_ahg,
        kishu_graph,
        kishu_incremental_checkpoint,
    ):
        """
        Test incremental store.
        """
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}), incremental_cr=True)
        planner_manager = PlannerManager(planner)

        # Run cell 1.
        x = []
        planner_manager.run_cell("1:1", {"x"}, {"x": x, "y": [x], "z": [x]}, "x = 1\ny = [x]\nz = [x]")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2.
        planner_manager.run_cell("1:2", {}, {}, "del z", {"z"})

        # Create and run checkpoint plan for cell 2.
        checkpoint_plan_cell2, _ = planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Assert that everything is stored again; {x, y} is a different VariableSnapshot vs. {x, y, z}.
        assert len(checkpoint_plan_cell2.actions) == 1
        assert len(checkpoint_plan_cell2.actions[0].vses_to_store) == 1
        assert checkpoint_plan_cell2.actions[0].vses_to_store[0].name == frozenset({"x", "y"})

    def test_checkpoint_restore_planner_incremental_restore_undo(
        self, db_path_name, enable_always_migrate, kishu_disk_ahg, kishu_graph, kishu_incremental_checkpoint
    ):
        """
        Test incremental restore with dynamically generated restore plan.
        """
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}), incremental_cr=True)
        planner_manager = PlannerManager(planner)

        # Run cell 1.
        planner_manager.run_cell("1:1", {}, {"x": 1, "y": 2}, "x = 1\ny = 2")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2. This modifies y and creates z.
        planner_manager.run_cell("1:2", {"y"}, {"y": 3, "z": 4}, "y += 1\nz = 4")

        # Create and run checkpoint plan for cell 2.
        planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        # Generate the incremental restore plan for undoing to cell 1.
        restore_plan = planner_manager.planner.generate_incremental_restore_plan(db_path_name, "1:1")

        # The restore plan consists of moving X and loading Y.
        version = min([ce.cell_num for ce in planner.get_ahg().get_all_cell_executions()])  # Get timestamp from stored CE
        assert len(restore_plan.actions) == 2
        assert len(restore_plan.actions[StepOrder.new_incremental_load(version)].variable_snapshots) == 1
        assert restore_plan.actions[StepOrder.new_move_variable(version)].vars_to_move.keyset() == {"x"}

    def test_checkpoint_restore_planner_incremental_restore_branch(
        self, db_path_name, enable_always_migrate, kishu_disk_ahg, kishu_graph, kishu_incremental_checkpoint
    ):
        """
        Test incremental restore with dynamically generated restore plan.
        """
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}), incremental_cr=True)
        planner_manager = PlannerManager(planner)

        # Run cell 1.
        planner_manager.run_cell("1:1", {}, {"x": 1, "y": 2}, "x = 1\ny = 2")

        # Create and run checkpoint plan for cell 1.
        planner_manager.checkpoint_session(db_path_name, "1:1", [])

        # Run cell 2.
        cell2_code = "y += 1\nz = 4\n"
        planner_manager.run_cell("1:2", {"y"}, {"y": 3, "z": 4}, cell2_code)

        # Create and run checkpoint plan for cell 2.
        planner_manager.checkpoint_session(db_path_name, "1:2", ["1:1"])

        """
            Generate the incremental restore plan for checking out from 1:2 to a hypothetical new branch with same active
            VSes as 1:2:
                 +- 1:2
            1:1 -+
                 +- target_state
        """
        # Generate the incremental restore plan for checking out from 1:2 to the new branch.
        restore_plan = planner_manager.planner._generate_incremental_restore_plan(
            db_path_name,
            planner.get_ahg().get_active_variable_snapshots("1:2"),
            planner.get_ahg().get_active_variable_snapshots("1:1"),
            ["1:1"],
        )

        version_1 = min([ce.cell_num for ce in planner.get_ahg().get_all_cell_executions()])  # Get timestamp from stored CE
        version_2 = max([ce.cell_num for ce in planner.get_ahg().get_all_cell_executions()])

        # The restore plan consists of moving X, loading Y, then rerunning cell 1
        # to modify x (to the version in cell 1) and recompute z.
        assert len(restore_plan.actions) == 3
        assert len(restore_plan.actions[StepOrder.new_incremental_load(version_1)].variable_snapshots) == 1
        assert restore_plan.actions[StepOrder.new_move_variable(version_1)].vars_to_move.keyset() == {"x"}
        assert restore_plan.actions[StepOrder.new_rerun_cell(version_2)].cell_code == cell2_code

    def test_get_differing_vars_post_checkout(
        self, db_path_name, enable_always_migrate, kishu_disk_ahg, kishu_graph, kishu_incremental_checkpoint
    ):
        """
        Tests the differing variables between pre and post-checkout are correctly identified.
        """
        planner = CheckpointRestorePlanner(kishu_disk_ahg, kishu_graph, Namespace({}), incremental_cr=True)
        planner_manager = PlannerManager(planner)

        # Run cell 1.
        planner_manager.run_cell("1:1", {}, {"x": 1, "y": 2}, "x = 1\ny = 2")

        # Run cell 2.
        cell2_code = "y += 1\nz = 4"
        planner_manager.run_cell("1:2", {"y"}, {"y": 3, "z": 4}, cell2_code)

        target_active_vses = planner.get_ahg().get_active_variable_snapshots("1:1")

        # Y needs to be updated when checking out from 1:2 to 1:1.
        assert planner_manager.planner._get_differing_vars_post_checkout(target_active_vses) == {"y"}
