from kishu.planning.variable_version_tracker import VariableVersionTracker


def test_update_variable_version():
    tracker = VariableVersionTracker({})
    tracker.update_variable_version("1", {"a"}, set())
    assert tracker.get_variable_versions() == {"a": "1"}

    tracker.update_variable_version("2", {"b"}, {"a"})
    assert tracker.get_variable_versions() == {"b": "2"}
