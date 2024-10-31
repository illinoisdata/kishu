import pytest

from IPython.core.interactiveshell import InteractiveShell

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VariableSnapshot, VersionedName
from kishu.planning.plan import CheckpointPlan, IncrementalCheckpointPlan, RestorePlan
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.path import KishuPath


UNDESERIALIZABLE_CLASS = """
class UndeserializableClass:
    def __init__(self):
        self.bar = 1
        self.baz = 2

    def __eq__(self, other):
        return self.bar == other.bar and self.baz == other.baz

    def __reduce__(self):
        return (self.__class__, (self.bar,))  # Purposely doesn't save self.baz

    def __getattr__(self, attr):
        if not self.baz:  # Infinite loop when unpickling
            pass
"""


class TestPlan:
    @pytest.fixture
    def db_path_name(self):
        return KishuPath.database_path("test")

    @pytest.fixture
    def kishu_checkpoint(self, db_path_name):
        """Fixture for initializing a KishuCheckpoint instance."""
        kishu_checkpoint = KishuCheckpoint(db_path_name)
        kishu_checkpoint.init_database()
        yield kishu_checkpoint
        kishu_checkpoint.drop_database()

    def test_checkout_wrong_id_error(self, db_path_name, kishu_checkpoint):
        exec_id = "abc"
        restore_plan = RestorePlan()
        restore_plan.add_load_variable_restore_action(1, ["a"], [(1, "a=1")])

        with pytest.raises(CommitIdNotExistError):
            restore_plan.run(db_path_name, exec_id)

    def test_store_everything_restore_plan(self, db_path_name, kishu_checkpoint):
        user_ns = Namespace({"a": 1, "b": 2})

        # save
        exec_id = 1
        checkpoint = CheckpointPlan.create(user_ns, db_path_name, exec_id)
        checkpoint.run(user_ns)

        # load
        restore_plan = RestorePlan()
        restore_plan.add_load_variable_restore_action(1, list(user_ns.keyset()), [(1, "a=1\nb=2")])
        result_ns = restore_plan.run(db_path_name, exec_id)

        assert result_ns.to_dict() == user_ns.to_dict()

    def test_recompute_everything_restore_plan(self, db_path_name, kishu_checkpoint):
        user_ns = Namespace({"a": 1, "b": 2})

        # save
        exec_id = 1
        checkpoint = CheckpointPlan.create(user_ns, db_path_name, exec_id)
        checkpoint.run(user_ns)

        # restore
        restore_plan = RestorePlan()
        restore_plan.add_rerun_cell_restore_action(1, "a=1\nb=2")
        result_ns = restore_plan.run(db_path_name, exec_id)

        assert result_ns.to_dict() == user_ns.to_dict()

    def test_mix_reload_recompute_restore_plan(self, db_path_name, kishu_checkpoint):
        user_ns = Namespace({"a": 1, "b": 2})

        # save
        exec_id = 1
        checkpoint = CheckpointPlan.create(user_ns, db_path_name, exec_id, var_names=["a"])
        checkpoint.run(user_ns)

        # restore
        restore_plan = RestorePlan()
        restore_plan.add_load_variable_restore_action(1, ["a"], [(1, "a=1")])
        restore_plan.add_rerun_cell_restore_action(2, "b=2")
        result_ns = restore_plan.run(db_path_name, exec_id)

        assert result_ns.to_dict() == user_ns.to_dict()

    def test_fallback_recomputation(self, db_path_name, kishu_checkpoint):
        shell = InteractiveShell()
        shell.run_cell(UNDESERIALIZABLE_CLASS)
        shell.run_cell("foo = UndeserializableClass()")

        user_ns = Namespace(shell.user_ns)
        filename = KishuPath.database_path("test")
        KishuCheckpoint(filename).init_database()

        # save
        exec_id = 1
        checkpoint = CheckpointPlan.create(user_ns, db_path_name, exec_id)
        checkpoint.run(user_ns)

        # restore
        restore_plan = RestorePlan()
        restore_plan.add_load_variable_restore_action(1, ["UndeserializableClass"], [(1, UNDESERIALIZABLE_CLASS)])
        restore_plan.add_load_variable_restore_action(2, ["foo"], [(2, "foo = UndeserializableClass()")])
        result_ns = restore_plan.run(db_path_name, exec_id)

        # Both load variable restored actions should have failed.
        assert len(restore_plan.fallbacked_actions) == 2

        # Compare keys in this case as modules are not directly comparable
        assert result_ns.keyset() == user_ns.keyset()
        assert result_ns["foo"] == user_ns["foo"]

    def test_store_versioned_names(self, db_path_name, enable_incremental_store, kishu_checkpoint):
        """
        Tests that the VARIABLE_SNAPSHOT table are populated correctly for incremental storage.
        TODO: add test for loading incrementally once that is implemented.
        """
        shell = InteractiveShell()
        shell.run_cell("a = 1")
        shell.run_cell("b = [a]")
        shell.run_cell("c = 2")

        user_ns = Namespace(shell.user_ns)

        # save
        exec_id = 1
        vses_to_store = [VariableSnapshot(frozenset({"a", "b"}), 1), VariableSnapshot(frozenset("c"), 1)]
        checkpoint = IncrementalCheckpointPlan.create(user_ns, db_path_name, exec_id, vses_to_store)
        checkpoint.run(user_ns)

        # Read stored versioned names
        stored_versioned_names = kishu_checkpoint.get_stored_versioned_names([exec_id])

        assert VersionedName(frozenset({"a", "b"}), 1), VersionedName(frozenset("c"), 1) in stored_versioned_names
