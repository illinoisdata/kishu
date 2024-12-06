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
    patched_shell.run_cell("y = x")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_augassign(namespace, patched_shell):
    # Test access by augassign.
    patched_shell.run_cell("x = 1")
    patched_shell.run_cell("x += 1")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_index(namespace, patched_shell):
    # Test access by indexing.
    patched_shell.run_cell("x = [1, 2, 3]")
    patched_shell.run_cell("y = x[0]")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_error_no_field(namespace, patched_shell):
    # Access is recorded even in the case of errors (x doesn't have field foo).
    patched_shell.run_cell("x = 1")
    patched_shell.run_cell("y = x.foo")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_vars_subfield(namespace, patched_shell):
    # Test access by subfield.
    patched_shell.run_cell("x = {1: 2}")
    patched_shell.run_cell("y = x.items()")
    assert namespace.accessed_vars() == {"x"}


def test_find_input_global(namespace, patched_shell):
    # Test access by global keyword.
    patched_shell.run_cell("x = 1")
    patched_shell.run_cell(
        """
            def func():
                global x
                x += 1
            func()
        """
    )
    assert namespace.accessed_vars() == {"func", "x"}


def test_special_inputs_magic(namespace, patched_shell):
    # Test compatibility with magic commands.
    patched_shell.run_cell("a = %who_ls")
    assert namespace.accessed_vars() == set()


def test_special_inputs_cmd(namespace, patched_shell):
    # Test compatibility with command-line inputs (!)
    patched_shell.run_cell("!pip install numpy")
    assert namespace.accessed_vars() == set()


def test_special_inputs_not_magic(namespace, patched_shell):
    patched_shell.run_cell("b = 2")
    patched_shell.run_cell("who_ls = 3")
    patched_shell.run_cell("a = b%who_ls")
    assert namespace.accessed_vars() == {"b", "who_ls"}


def test_input_decorator(namespace, patched_shell):
    patched_shell.run_cell(
        """
        def my_decorator(func):
            def wrapper():
                print("Something before the function.")
                func()
                print("Something after the function.")
            return wrapper
    """
    )
    patched_shell.run_cell(
        """
        @my_decorator
        def say_hello():
            print("Hello!")
    """
    )
    assert namespace.accessed_vars() == {"my_decorator"}


def test_input_subclass(namespace, patched_shell):
    patched_shell.run_cell(
        """
        class MyClass:
            pass
    """
    )
    patched_shell.run_cell(
        """
        class MySubClass(MyClass):
            pass
    """
    )
    assert namespace.accessed_vars() == {"MyClass"}


def test_find_assigned_vars_augassign(namespace, patched_shell):
    # Test assigning via overwrite.
    patched_shell.run_cell("x = 1")
    patched_shell.run_cell("x += 1")
    assert namespace.assigned_vars() == {"x"}


def test_find_assigned_vars_overwrite(namespace, patched_shell):
    # Test assigning via overwrite.
    patched_shell.run_cell("x = 1")
    patched_shell.run_cell("x = 2")
    assert namespace.assigned_vars() == {"x"}


def test_find_assigned_vars_error(namespace, patched_shell):
    # Test assigning via overwrite.
    patched_shell.run_cell("x = 1")
    patched_shell.run_cell("x = y")  # This assignment did not go through as finding y precedes assigning to x.
    assert namespace.assigned_vars() == set("x")


def test_find_assign_global(namespace, patched_shell):
    """
    See https://github.com/python/cpython/blob/6cf77949fba7b44f6885794b2028f091f42f5d6c/Python/generated_cases.c.h#L7534
    for why PatchedNamespace does not detect global assignments:
        int err = PyDict_SetItem(GLOBALS(), name, PyStackRef_AsPyObjectBorrow(v));
    STORE_NAME calls the internal (C) setter of the dictionary if the globals dictionary is a vanilla python dictionary,
    and __setitem__ otherwise (e.g., globals is PatchedNamespace). However, STORE_GLOBAL always calls the former; it is
    likely unintended, given that LOAD_NAME and LOAD_GLOBAL makes no such distinctions.
    """
    # Test access by global keyword.
    patched_shell.run_cell("x = 1")
    namespace.reset_assigned_vars()
    patched_shell.run_cell(
        """
            def func():
                global x
                x += 1
            func()
        """
    )
    assert namespace.assigned_vars() == {"func"}


def test_find_assign_function(namespace, patched_shell):
    # Test assignment by function declaration.
    patched_shell.run_cell(
        """
            def func():
                pass
        """
    )
    assert namespace.assigned_vars() == {"func"}


def test_find_assign_class(namespace, patched_shell):
    # Test assignment by class declaration.
    patched_shell.run_cell(
        """
            class Test:
                pass
        """
    )
    assert namespace.assigned_vars() == {"Test"}


def test_find_assign_import(namespace, patched_shell):
    # Test assignment by class declaration.
    patched_shell.run_cell(
        """
            import pickle
        """
    )
    patched_shell.run_cell(
        """
            import numpy as np
        """
    )
    assert namespace.assigned_vars() == {"pickle", "np"}


def test_find_assign_try_except(namespace, patched_shell):
    # Test assignment by class declaration.
    patched_shell.run_cell(
        """
            try:
                print(x)  # error
            except Exception as e:
                pass
        """
    )
    assert namespace.assigned_vars() == {"e"}


def test_find_assign_with(namespace, patched_shell):
    # Test assignment by class declaration.
    patched_shell.run_cell(
        """
            import threading
            lock = threading.Lock()
            with lock as lock2:
                pass
        """
    )
    assert namespace.assigned_vars() == {"threading", "lock", "lock2"}


def test_find_assign_forloop(namespace, patched_shell):
    # Test assignment by class declaration.
    patched_shell.run_cell(
        """
            for i in range(10):
                pass
        """
    )
    assert namespace.assigned_vars() == {"i"}


def test_find_assign_if(namespace, patched_shell):
    # X should not have been assigned.
    patched_shell.run_cell(
        """
            if 1 > 2:
                x = 1
        """
    )
    assert namespace.assigned_vars() == set()
