from kishu.planning.change import find_input_vars, find_created_and_deleted_vars


def test_find_input_vars():
    """
       TODO: add more test cases when recursing into UDFs is supported.
    """
    # Test access by name.
    code_cell_1 = "print(x)"
    input_vars_1 = find_input_vars(code_cell_1, {"x"}, {"x": 1}, set())

    assert input_vars_1 == {"x"}

    # Test access by augassign.
    code_cell_2 = "x += 1"
    input_vars_2 = find_input_vars(code_cell_2, {"x"}, {"x": 1}, set())

    assert input_vars_2 == {"x"}

    # Test access by indexing.
    code_cell_3 = "print(x[0])"
    input_vars_3 = find_input_vars(code_cell_3, {"x"}, {"x": [1, 2, 3]}, set())

    assert input_vars_3 == {"x"}

    # Test access by subfield.
    code_cell_4 = "print(x.foo)"
    input_vars_4 = find_input_vars(code_cell_4, {"x"}, {"x": [1, 2, 3]}, set())

    assert input_vars_4 == {"x"}


def test_special_inputs():
    """
        Test that the parser does not break on special commands (e.g., magics, console comands)
    """
    code_cell_1 = "a = %who_ls"
    input_vars_1 = find_input_vars(code_cell_1, {}, {}, set())

    assert input_vars_1 == set()

    code_cell_2 = "%matplotlib inline"
    input_vars_2 = find_input_vars(code_cell_2, {}, {}, set())

    assert input_vars_2 == set()

    code_cell_3 = "!pip install numpy"
    input_vars_3 = find_input_vars(code_cell_3, {}, {}, set())

    assert input_vars_3 == set()

    # The who_ls here is not a magic. b and who_ls should be recognized as accessed for the modulo operator.
    code_cell_4 = "a = b%who_ls"
    input_vars_4 = find_input_vars(code_cell_4, {"b", "who_ls"}, {"b": 2, "who_ls": 3}, set())

    assert input_vars_4 == {"b", "who_ls"}


def test_find_created_and_deleted_vars():
    pre_execution_1 = {"x", "y"}
    post_execution_1 = {"y", "z"}

    created_vars_1, deleted_vars_1 = find_created_and_deleted_vars(pre_execution_1, post_execution_1)

    assert created_vars_1 == {"z"}
    assert deleted_vars_1 == {"x"}

    # Variables with underscores are skipped.
    pre_execution_2 = {"_x", "y"}
    post_execution_2 = {"y", "_z"}

    created_vars_2, deleted_vars_2 = find_created_and_deleted_vars(pre_execution_2, post_execution_2)

    assert created_vars_2 == set()
    assert deleted_vars_2 == set()
