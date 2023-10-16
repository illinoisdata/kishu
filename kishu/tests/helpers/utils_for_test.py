import os

from contextlib import contextmanager


@contextmanager
def environment_variable(key, value):
    """
    Temporarily sets an environment variable within a context.
    """
    original_value = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if original_value is None:
            del os.environ[key]
        else:
            os.environ[key] = original_value
