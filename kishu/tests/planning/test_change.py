from kishu.planning.change import find_created_and_deleted_vars


def test_find_created_and_deleted_vars():
    pre_execution_1 = {"x", "y"}
    post_execution_1 = {"y", "z"}

    created_vars_1, deleted_vars_1 = find_created_and_deleted_vars(pre_execution_1, post_execution_1)

    assert created_vars_1 == {"z"}
    assert deleted_vars_1 == {"x"}


def test_find_created_and_deleted_vars_skip_underscores():
    # Variables with underscores are skipped.
    pre_execution_2 = {"_x", "y"}
    post_execution_2 = {"y", "_z"}

    created_vars_2, deleted_vars_2 = find_created_and_deleted_vars(pre_execution_2, post_execution_2)

    assert created_vars_2 == set()
    assert deleted_vars_2 == set()
