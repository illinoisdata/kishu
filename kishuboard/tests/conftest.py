import pytest
from kishuboard.server import app as kishuboard_app
# from kishuboard.kishuboard.server import app as kishuboard_app

@pytest.fixture()
def backend_client():
    return kishuboard_app.test_client()