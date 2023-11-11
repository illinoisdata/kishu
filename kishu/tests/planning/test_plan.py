import pytest

from pathlib import Path

from kishu.jupyter.namespace import Namespace
from kishu.planning.plan import LoadVariableRestoreAction, StoreEverythingCheckpointPlan
from kishu.storage.checkpoint import KishuCheckpoint


def test_checkout_wrong_id_error(tmp_path: Path):
    filename = str(tmp_path / "ckpt.sqlite")
    KishuCheckpoint(filename).init_database()

    exec_id = 'abc'
    restore_ns = {}
    restore = LoadVariableRestoreAction()

    with pytest.raises(Exception):
        restore.run(restore_ns, filename, exec_id)


def test_save_everything_checkpoint_plan(tmp_path: Path):
    user_ns = Namespace({
        'a': 1,
        'b': 2
    })
    filename = str(tmp_path / "ckpt.sqlite")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = StoreEverythingCheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # load
    restore_ns = Namespace({})
    restore = LoadVariableRestoreAction()
    restore.run(restore_ns, filename, exec_id)

    assert restore_ns == user_ns


def test_store_everything_generated_restore_plan(tmp_path: Path):
    user_ns = Namespace({
        'a': 1,
        'b': 2
    })
    filename = str(tmp_path / "ckpt.sqlite")
    KishuCheckpoint(filename).init_database()

    # save
    exec_id = 1
    checkpoint = StoreEverythingCheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # restore
    restore_ns = Namespace({})
    restore = checkpoint.restore_plan()
    restore.run(restore_ns, filename, exec_id)

    assert restore_ns == user_ns
