import os
import pytest

from pathlib import Path
from typing import Generator, Type

from kishu.backend import app as kishu_app
from kishu.storage.path import ENV_KISHU_PATH_ROOT, KishuPath


# Use this fixture to mount Kishu in a temporary directory in the same process.
@pytest.fixture()
def tmp_kishu_path(tmp_path: Path) -> Generator[Type[KishuPath], None, None]:
    original_root = KishuPath.ROOT
    KishuPath.ROOT = str(tmp_path)
    yield KishuPath
    KishuPath.ROOT = original_root


# Use this fixture to mount Kishu in a temporary directory across processes.
@pytest.fixture()
def tmp_kishu_path_os(tmp_path: Path) -> Generator[Type[KishuPath], None, None]:
    original_root = os.environ.get(ENV_KISHU_PATH_ROOT, None)
    os.environ[ENV_KISHU_PATH_ROOT] = str(tmp_path)
    yield KishuPath
    if original_root is not None:
        os.environ[ENV_KISHU_PATH_ROOT] = original_root


@pytest.fixture()
def backend_client():
    return kishu_app.test_client()
