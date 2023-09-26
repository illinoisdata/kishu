import pytest

from kishu.checkpoint_io import init_checkpoint_database
from kishu.plan import LoadVariableRestoreAction, StoreEverythingCheckpointPlan
from tempfile import NamedTemporaryFile


def test_checkout_wrong_id_error():
    checkpoint_file = NamedTemporaryFile()
    filename = checkpoint_file.name
    init_checkpoint_database(filename)

    exec_id = 'abc'
    restore_ns = {}
    restore = LoadVariableRestoreAction()

    with pytest.raises(Exception):
        restore.run(restore_ns, filename, exec_id)


def test_save_everything_checkpoint_plan():
    user_ns = {
        'a': 1,
        'b': 2
    }
    checkpoint_file = NamedTemporaryFile()
    filename = checkpoint_file.name
    init_checkpoint_database(filename)

    # save
    exec_id = 1
    checkpoint = StoreEverythingCheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # load
    restore_ns = {}
    restore = LoadVariableRestoreAction()
    restore.run(restore_ns, filename, exec_id)

    assert restore_ns == user_ns


def test_store_everything_generated_restore_plan():
    user_ns = {
        'a': 1,
        'b': 2
    }
    checkpoint_file = NamedTemporaryFile()
    filename = checkpoint_file.name
    init_checkpoint_database(filename)

    # save
    exec_id = 1
    checkpoint = StoreEverythingCheckpointPlan.create(user_ns, filename, exec_id)
    checkpoint.run(user_ns)

    # restore
    restore_ns = {}
    restore = checkpoint.restore_plan()
    restore.run(restore_ns, filename, exec_id)

    assert restore_ns == user_ns
