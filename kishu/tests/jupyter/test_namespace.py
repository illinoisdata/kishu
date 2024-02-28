FUNC_GLOBAL_ACCESS = """
    def func():
        global x
        x += 1
    func()
"""


def test_find_input_vars(monkey_patch_ns):
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("x = 1")
    shell.run_cell("x")
    assert namespace.get_accessed_vars() == {"x"}


def test_find_input_vars_augassign(monkey_patch_ns):
    # Test access by augassign.
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("x = 1")
    shell.run_cell("x += 1")
    assert namespace.get_accessed_vars() == {"x"}


def test_find_input_vars_index(monkey_patch_ns):
    # Test access by indexing.
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("x = [1, 2, 3]")
    shell.run_cell("x[0]")
    assert namespace.get_accessed_vars() == {"x"}


def test_find_input_vars_subfield(monkey_patch_ns):
    # Test access by subfield.
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("x = {1: 2}")
    shell.run_cell("x.items()")
    assert namespace.get_accessed_vars() == {"x"}


def test_find_input_global(monkey_patch_ns):
    # Test access by global keyword.
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("x = 1")
    shell.run_cell(FUNC_GLOBAL_ACCESS)
    assert namespace.get_accessed_vars() == {"func", "x"}


def test_special_inputs_magic(monkey_patch_ns):
    # Test compatibility with magic commands.
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("a = %who_ls")
    assert namespace.get_accessed_vars() == set()


def test_special_inputs_magic2(monkey_patch_ns):
    # Test compatibility with magic commands.
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("%matplotlib inline")
    assert namespace.get_accessed_vars() == set()


def test_special_inputs_cmd(monkey_patch_ns):
    # Test compatibility with command-line inputs (!)
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("!pip install numpy")
    assert namespace.get_accessed_vars() == set()


def test_special_inputs_not_magic(monkey_patch_ns):
    shell = monkey_patch_ns[0]
    namespace = monkey_patch_ns[1]

    shell.run_cell("b = 2")
    shell.run_cell("who_ls = 3")
    shell.run_cell("a = b%who_ls")
    assert namespace.get_accessed_vars() == {"b", "who_ls"}
