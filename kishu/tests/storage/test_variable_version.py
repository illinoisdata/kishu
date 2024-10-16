from kishu.storage.path import KishuPath
from kishu.storage.variable_version import VariableVersion


def test_variable_version_table(nb_simple_path):
    kishu_var_version = VariableVersion(KishuPath.database_path(nb_simple_path))
    kishu_var_version.init_database()
    kishu_var_version.store_variable_version_table({"a", "b"}, "1")
    kishu_var_version.store_variable_version_table({"a", "c"}, "2")
    kishu_var_version.store_variable_version_table({"b", "c"}, "3")
    assert kishu_var_version.get_commit_ids_by_variable_name("a") == ["1", "2"]
    assert kishu_var_version.get_commit_ids_by_variable_name("b") == ["1", "3"]
    assert kishu_var_version.get_commit_ids_by_variable_name("c") == ["2", "3"]


def test_commit_variable_version_table(nb_simple_path):
    kishu_var_version = VariableVersion(KishuPath.database_path(nb_simple_path))
    kishu_var_version.init_database()
    kishu_var_version.store_commit_variable_version_table("1", {"a": "1", "b": "1"})
    kishu_var_version.store_commit_variable_version_table("2", {"b": "1", "a": "2", "c": "2"})
    kishu_var_version.store_commit_variable_version_table("3", {"a": "2", "b": "3", "c": "3"})
    assert kishu_var_version.get_variable_version_by_commit_id("1") == {"a": "1", "b": "1"}
    assert kishu_var_version.get_variable_version_by_commit_id("2") == {"b": "1", "a": "2", "c": "2"}
    assert kishu_var_version.get_variable_version_by_commit_id("3") == {"a": "2", "b": "3", "c": "3"}
    assert kishu_var_version.get_variable_version_by_commit_id("4") == {}
