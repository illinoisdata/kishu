import pytest
from IPython.core.interactiveshell import InteractiveShell

from kishu.jupyter.namespace import Namespace


class ShellManager:
    def __init__(self, namespace: Namespace, managed_shell: InteractiveShell):
        self._shell = managed_shell
        self._namespace = namespace

    def run_cell(self, cell_code: str) -> None:
        self._namespace.set_vars_to_track(self._namespace.keyset())
        self._shell.run_cell(cell_code)


@pytest.fixture()
def shell():
    return InteractiveShell()


@pytest.fixture()
def namespace():  # Or namespace(shell)
    return Namespace({})


@pytest.fixture
def shell_manager(shell, namespace) -> ShellManager:
    shell.init_create_namespaces(
        user_module=None,
        user_ns=namespace.get_tracked_namespace(),
    )
    return ShellManager(namespace, shell)


def test_find_input_vars(namespace, shell_manager):
    shell_manager.run_cell("x = 1")
    shell_manager.run_cell("y = x")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_augassign(namespace, shell_manager):
    # Test access by augassign.
    shell_manager.run_cell("x = 1")
    shell_manager.run_cell("x += 1")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_index(namespace, shell_manager):
    # Test access by indexing.
    shell_manager.run_cell("x = [1, 2, 3]")
    shell_manager.run_cell("y = x[0]")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_error_no_var(namespace, shell_manager):
    # Access is not recorded as x doesn't exist.
    shell_manager.run_cell("y = x")
    assert namespace.accessed_vars() == set()


def test_find_input_vars_error_no_field(namespace, shell_manager):
    # Access is recorded even in the case of errors (x doesn't have field foo).
    shell_manager.run_cell("x = 1")
    shell_manager.run_cell("y = x.foo")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_subfield(namespace, shell_manager):
    # Test access by subfield.
    shell_manager.run_cell("x = {1: 2}")
    shell_manager.run_cell("y = x.items()")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_global_assign(namespace, shell_manager):
    # Test access by global keyword.
    shell_manager.run_cell("x = 1")
    shell_manager.run_cell(
        """
            def func():
                global x
                x += 1
            func()
        """
    )
    assert namespace.accessed_vars() == {"x"}


def test_special_inputs_magic(namespace, shell_manager):
    # Test compatibility with magic commands.
    shell_manager.run_cell("a = %who_ls")
    assert namespace.accessed_vars() == set()


def test_special_inputs_cmd(namespace, shell_manager):
    # Test compatibility with command-line inputs (!)
    shell_manager.run_cell("!pip install numpy")
    assert namespace.accessed_vars() == set()


def test_special_inputs_not_magic(namespace, shell_manager):
    shell_manager.run_cell("b = 2")
    shell_manager.run_cell("who_ls = 3")
    shell_manager.run_cell("a = b%who_ls")
    assert namespace.accessed_vars() == {"b", "who_ls"}


def test_find_assigned_vars_augassign(namespace, shell_manager):
    # Test assigning via overwrite.
    shell_manager.run_cell("x = 1")
    shell_manager.run_cell("x += 1")
    assert namespace.assigned_vars() == {"x"}


def test_find_assigned_vars_overwrite(namespace, shell_manager):
    # Test assigning via overwrite.
    shell_manager.run_cell("x = 1")
    shell_manager.run_cell("x = 2")
    assert namespace.assigned_vars() == {"x"}


def test_find_assigned_vars_redefine(namespace, shell_manager):
    shell_manager.run_cell(
        """
            def func():
                print("hello")
        """
    )
    shell_manager.run_cell(
        """
            def func():
                print("world")
        """
    )
    assert namespace.assigned_vars() == {"func"}
