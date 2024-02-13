import pytest

from IPython.core.interactiveshell import InteractiveShell

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.planning.plan import CheckpointPlan, RestorePlan
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.path import KishuPath


def test_checkout_wrong_id_error():
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    exec_id = 'abc'
    restore_plan = RestorePlan()
    restore_plan.add_load_variable_restore_action(1,
                                                  ["a"],
                                                  [(1, "a=1")])

    with pytest.raises(CommitIdNotExistError):
        restore_plan.run(filename, exec_id)


def test_store_everything_restore_plan():
    user_ns = Namespace({
        'a': 1,
        'b': 2
    })
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = CheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # load
    restore_plan = RestorePlan()
    restore_plan.add_load_variable_restore_action(1,
                                                  list(user_ns.keyset()),
                                                  [(1, "a=1\nb=2")])
    result_ns = restore_plan.run(filename, exec_id)

    assert result_ns.to_dict() == user_ns.to_dict()


def test_recompute_everything_restore_plan():
    user_ns = Namespace({
        'a': 1,
        'b': 2
    })
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = CheckpointPlan.create(user_ns, filename, exec_id, var_names=[])
    checkpoint.run(user_ns)

    # restore
    restore_plan = RestorePlan()
    restore_plan.add_rerun_cell_restore_action(1, "a=1\nb=2")
    result_ns = restore_plan.run(filename, exec_id)

    assert result_ns.to_dict() == user_ns.to_dict()


def test_mix_reload_recompute_restore_plan():
    user_ns = Namespace({
        'a': 1,
        'b': 2
    })
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = CheckpointPlan.create(user_ns, filename, exec_id, var_names=["a"])
    checkpoint.run(user_ns)

    # restore
    restore_plan = RestorePlan()
    restore_plan.add_load_variable_restore_action(1,
                                                  ["a"],
                                                  [(1, "a=1")])
    restore_plan.add_rerun_cell_restore_action(2, "b=2")
    result_ns = restore_plan.run(filename, exec_id)

    assert result_ns.to_dict() == user_ns.to_dict()


def test_fallback_recomputation():
    shell = InteractiveShell()
    shell.run_cell("from qiskit import Aer")
    shell.run_cell("sim = Aer.get_backend('aer_simulator')")

    user_ns = Namespace(shell.user_ns)
    filename = KishuPath.database_path("test")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = CheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # restore
    restore_plan = RestorePlan()
    restore_plan.add_load_variable_restore_action(1,
                                                  ["Aer"],
                                                  [(1, "from qiskit import Aer")])
    restore_plan.add_load_variable_restore_action(2,
                                                  ["sim"],
                                                  [(2, "sim = Aer.get_backend('aer_simulator')")])
    result_ns = restore_plan.run(filename, exec_id)

    # Both load variable restored actions should have failed.
    assert len(restore_plan.fallbacked_actions) == 2

    # Compare keys in this case as modules are not directly comparable
    assert result_ns.keyset() == user_ns.keyset()
    assert result_ns["Aer"] == user_ns["Aer"]
    assert str(result_ns["sim"]) == str(user_ns["sim"])
