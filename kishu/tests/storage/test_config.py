import configparser
import os
import time

import pytest

from kishu.storage.config import Config, PersistentConfig
from kishu.storage.path import KishuPath


def test_initialize_config_get_default(tmp_path_config):
    # Assert default categories exist.
    for category in Config.DEFAULT_CATEGORIES:
        assert category in Config.config

    # Check that the field has not been previously set.
    assert "nonexistant_field" not in Config.config["PLANNER"]

    # When the field doesn't exist, the default value is returned.
    assert Config.get("PLANNER", "nonexistant_field", "1") == "1"


def test_set_and_get_new_fields(tmp_path_config):
    assert "PLANNER" in Config.config

    # Test with string.
    assert "string_field" not in Config.config["PLANNER"]
    Config.set("PLANNER", "string_field", "42")
    assert Config.get("PLANNER", "string_field", "0") == "42"

    # Test with int.
    assert "int_field" not in Config.config["PLANNER"]
    Config.set("PLANNER", "int_field", 42)
    assert Config.get("PLANNER", "int_field", 0) == 42


def test_set_and_get_update_fields(tmp_path_config):
    assert "PROFILER" in Config.config

    # Check that the field has not been previously set.
    assert "excluded_modules" not in Config.config["PROFILER"]
    Config.set("PROFILER", "excluded_modules", ["a"])
    assert Config.get("PROFILER", "excluded_modules", []) == ["a"]

    # Check that the field is updated.
    Config.set("PROFILER", "excluded_modules", ["1", "2"])
    assert Config.get("PROFILER", "excluded_modules", []) == ["1", "2"]


def test_concurrent_update_field(tmp_path_config):
    """
    Tests the config file can be updated by a second kishu instance / configparser.
    """
    assert "PLANNER" in Config.config

    # Set a string field.
    assert "string_field" not in Config.config["PLANNER"]
    Config.set("PLANNER", "string_field", "42")
    assert Config.get("PLANNER", "string_field", "0") == "42"

    # Second parser which will update the config file.
    second_parser = configparser.ConfigParser()
    second_parser.read(Config.CONFIG_PATH)

    # For preventing race conditions related to st_mtime_ns.
    time.sleep(0.01)

    # Second parser updates the config file.
    assert "PLANNER" in second_parser
    assert "string_field" in second_parser["PLANNER"]
    second_parser["PLANNER"]["string_field"] = "2119"
    with open(Config.CONFIG_PATH, "w") as configfile2:
        second_parser.write(configfile2)

    # The field should be updated correctly.
    assert Config.get("PLANNER", "string_field", "0") == "2119"


def test_skip_reread(tmp_path_config):
    """
    Tests accessing a config value when the config file has not been updated
    skips the file read.
    """
    assert "PLANNER" in Config.config

    Config.set("PLANNER", "test_field1", 1)
    Config.set("PLANNER", "test_field2", 2)

    assert Config.get("PLANNER", "test_field1", 0) == 1
    first_read_time = os.path.getatime(Config.CONFIG_PATH)
    assert Config.get("PLANNER", "test_field2", 0) == 2
    second_read_time = os.path.getatime(Config.CONFIG_PATH)

    # The second call to config.get does not result in the config file being read again.
    assert first_read_time == second_read_time


def test_manual_bad_write(tmp_path_config):
    # For preventing race conditions related to st_mtime_ns.
    time.sleep(0.01)

    # Manually write garbage into the config file.
    with open(Config.CONFIG_PATH, "wb") as configfile:
        configfile.write(b"abcdefg")
        configfile.flush()
        os.fsync(configfile.fileno())

    # Assert reading the config file fails.
    with pytest.raises(configparser.MissingSectionHeaderError):
        assert Config.get("PROFILER", "excluded_modules", []) == ["a"]


def test_set_and_get_nonexistant_category(tmp_path_config):
    assert "ABCDEFG" not in Config.config

    # Check that accessing a nonexistant category throws an error.
    with pytest.raises(KeyError):
        Config.get("ABCDEFG", "abcdefg", 1)

    # Check that writing to a nonexistant category throws an error.
    with pytest.raises(KeyError):
        Config.set("ABCDEFG", "abcdefg", 1)


def test_boolean_config(tmp_path_config):
    # Check that boolean fields are correctly casted, i.e., the "False" written to the config file is correctly parsed.
    assert "always_migrate" not in Config.config["OPTIMIZER"]
    Config.set("OPTIMIZER", "always_migrate", False)
    assert not Config.get("OPTIMIZER", "always_migrate", True)

    Config.set("OPTIMIZER", "always_migrate", 0)
    assert not Config.get("OPTIMIZER", "always_migrate", True)

    Config.set("OPTIMIZER", "always_migrate", "no")
    assert not Config.get("OPTIMIZER", "always_migrate", True)

    Config.set("OPTIMIZER", "always_migrate", True)
    assert Config.get("OPTIMIZER", "always_migrate", False)

    Config.set("OPTIMIZER", "always_migrate", 1)
    assert Config.get("OPTIMIZER", "always_migrate", False)

    Config.set("OPTIMIZER", "always_migrate", "yes")
    assert Config.get("OPTIMIZER", "always_migrate", False)

    # Non-bools throw an error when parsed.
    Config.set("OPTIMIZER", "always_migrate", "ABC")
    with pytest.raises(ValueError):
        _ = Config.get("OPTIMIZER", "always_migrate", True)


class TestPersistentConfig:
    @pytest.fixture
    def db_path_name(self, nb_simple_path):
        return KishuPath.database_path(nb_simple_path)

    @pytest.fixture
    def persistent_config(self, db_path_name):
        """Fixture for initializing a KishuBranch instance."""
        persistent_config = PersistentConfig(db_path_name)
        persistent_config.init_database()
        yield persistent_config
        persistent_config.drop_database()

    def test_set_persistent_config(self, persistent_config):
        # Set the fields in config.
        Config.set("PLANNER", "string_field", "42")
        Config.set("PROFILER", "excluded_modules", ["a"])

        # Set the fields in persistent config.
        persistent_config._set_from_config("PLANNER", "string_field", "42")
        persistent_config._set_from_config("PROFILER", "excluded_modules", ["a"])

        # Assert that the set fields exist.
        assert persistent_config.get("PROFILER", "excluded_modules", []) == ["a"]

        # Assert that the set field is persistent even if the original config is changed.
        Config.set("PLANNER", "string_field", "43")
        assert persistent_config.get("PLANNER", "string_field", "43") == "42"

    def test_get_dynamically_populated_field(self, persistent_config):
        assert persistent_config.get("PLANNER", "string_field", "42") == "42"
