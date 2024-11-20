import pytest
from IPython.core.interactiveshell import InteractiveShell

from kishu.jupyter.namespace import Namespace


@pytest.fixture()
def shell():
    return InteractiveShell()


@pytest.fixture()
def namespace():  # Or namespace(shell)
    return Namespace({})


@pytest.fixture
def patched_shell(shell, namespace):
    shell.init_create_namespaces(
        user_module=None,
        user_ns=namespace.get_tracked_namespace(),
    )
    return shell


def test_find_input_vars(namespace, patched_shell):
    patched_shell.run_cell("x = 1")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell("y = x")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_augassign(namespace, patched_shell):
    # Test access by augassign.
    patched_shell.run_cell("x = 1")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell("x += 1")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_index(namespace, patched_shell):
    # Test access by indexing.
    patched_shell.run_cell("x = [1, 2, 3]")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell("y = x[0]")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_error_no_var(namespace, patched_shell):
    # Access is not recorded as x doesn't exist.
    patched_shell.run_cell("y = x")
    namespace.set_vars_to_track({"x"})
    assert namespace.accessed_vars() == set()


def test_find_input_vars_error_no_field(namespace, patched_shell):
    # Access is recorded even in the case of errors (x doesn't have field foo).
    patched_shell.run_cell("x = 1")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell("y = x.foo")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_subfield(namespace, patched_shell):
    # Test access by subfield.
    patched_shell.run_cell("x = {1: 2}")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell("y = x.items()")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_global_assign(namespace, patched_shell):
    # Test access by global keyword.
    patched_shell.run_cell("x = 1")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell(
        """
            def func():
                global x
                x += 1
            func()
        """
    )
    assert namespace.accessed_vars() == {"x"}


def test_special_inputs_magic(namespace, patched_shell):
    # Test compatibility with magic commands.
    patched_shell.run_cell("a = %who_ls")
    namespace.set_vars_to_track({"a"})
    assert namespace.accessed_vars() == set()


def test_special_inputs_cmd(namespace, patched_shell):
    # Test compatibility with command-line inputs (!)
    patched_shell.run_cell("!pip install numpy")
    assert namespace.accessed_vars() == set()


def test_special_inputs_not_magic(namespace, patched_shell):
    patched_shell.run_cell("b = 2")
    namespace.set_vars_to_track({"b"})
    patched_shell.run_cell("who_ls = 3")
    namespace.set_vars_to_track({"b", "who_ls"})
    patched_shell.run_cell("a = b%who_ls")
    assert namespace.accessed_vars() == {"b", "who_ls"}


def test_find_assigned_vars_augassign(namespace, patched_shell):
    # Test assigning via overwrite.
    patched_shell.run_cell("x = 1")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell("x += 1")
    assert namespace.assigned_vars() == {"x"}


def test_find_assigned_vars_overwrite(namespace, patched_shell):
    # Test assigning via overwrite.
    patched_shell.run_cell("x = 1")
    namespace.set_vars_to_track({"x"})
    patched_shell.run_cell("x = 2")
    assert namespace.assigned_vars() == {"x"}


def test_find_assigned_vars_redefine(namespace, patched_shell):
    patched_shell.run_cell(
        """
            def func():
                print("hello")
        """
    )
    namespace.set_vars_to_track({"func"})
    patched_shell.run_cell(
        """
            def func():
                print("world")
        """
    )
    assert namespace.assigned_vars() == {"func"}
