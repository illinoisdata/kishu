import json
from kishu.commands import (
    ListResult,
    LogResult,
)
from kishu.storage.branch import HeadBranch


def test_health(backend_client):
    result = backend_client.get("/api/health")
    data = json.loads(result.data.decode())
    assert data["status"] == "ok"


def test_list_empty(backend_client):
    result = backend_client.get("/api/list")
    assert result.status_code == 200
    assert ListResult.from_json(result.data) == ListResult(sessions=[])

    result = backend_client.get("/api/list?list_all=true")
    assert result.status_code == 200
    assert ListResult.from_json(result.data) == ListResult(sessions=[])


def test_log_empty(backend_client):
    result = backend_client.get("/api/log/NON_EXISTENT_NOTEBOOK_ID")
    assert result.status_code == 200
    assert LogResult.from_json(result.data) == LogResult(
        commit_graph=[],
        head=HeadBranch(branch_name=None, commit_id=None),
    )
