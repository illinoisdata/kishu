import pytest

from pathlib import Path

from kishu.jupyter.namespace import Namespace
from kishu.planning.plan import CheckpointPlan, RestorePlan
from kishu.storage.checkpoint import KishuCheckpoint


def test_checkout_wrong_id_error(tmp_path: Path):
    filename = str(tmp_path / "ckpt.sqlite")
    KishuCheckpoint(filename).init_database()

    exec_id = 'abc'
    restore_plan = RestorePlan()
    restore_plan.add_load_variable_restore_action([])

    with pytest.raises(Exception):
        restore_plan.run(filename, exec_id)


def test_save_everything_checkpoint_plan(tmp_path: Path):
    user_ns = Namespace({
        'a': 1,
        'b': 2
    })
    filename = str(tmp_path / "ckpt.sqlite")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = CheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # load
    restore_plan = RestorePlan()
    restore_plan.add_load_variable_restore_action(list(user_ns.keyset()))
    result_ns = restore_plan.run(filename, exec_id)

    assert result_ns.to_dict() == user_ns.to_dict()


def test_store_everything_generated_restore_plan(tmp_path: Path):
    user_ns = Namespace({
        'a': 1,
        'b': 2
    })
    filename = str(tmp_path / "ckpt.sqlite")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = CheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # restore
    restore_plan = RestorePlan()
    restore_plan.add_load_variable_restore_action(list(user_ns.keyset()))
    result_ns = restore_plan.run(filename, exec_id)

    assert result_ns.to_dict() == user_ns.to_dict()
