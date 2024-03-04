import configparser
import os
import pytest
import time

from kishu.storage.config import Config


def test_initialize_config_get_default():
    # The config file should not exist before the first get call.
    assert not os.path.isfile(Config.CONFIG_PATH)

    # Assert default categories exist.
    for category in Config.DEFAULT_CATEGORIES:
        assert category in Config.config

    # Check that the field has not been previously set.
    assert 'nonexistant_field' not in Config.config['PLANNER']

    # When the field doesn't exist, the default value is returned.
    assert Config.get('PLANNER', 'nonexistant_field', "1") == "1"


def test_set_and_get_new_fields():
    assert 'PLANNER' in Config.config

    # Test with string.
    assert 'string_field' not in Config.config['PLANNER']
    Config.set('PLANNER', 'string_field', '42')
    assert Config.get('PLANNER', 'string_field', '0') == '42'

    # Test with int.
    assert 'int_field' not in Config.config['PLANNER']
    Config.set('PLANNER', 'int_field', 42)
    assert Config.get('PLANNER', 'int_field', 0) == 42


def test_set_and_get_update_fields():
    assert 'PROFILER' in Config.config

    # Check that the field has not been previously set.
    assert 'excluded_modules' not in Config.config['PROFILER']
    Config.set('PROFILER', 'excluded_modules', ["a"])
    assert Config.get('PROFILER', 'excluded_modules', []) == ["a"]

    # Check that the field is updated.
    Config.set('PROFILER', 'excluded_modules', ["1", "2"])
    assert Config.get('PROFILER', 'excluded_modules', []) == ["1", "2"]


def test_concurrent_update_field():
    """
        Tests the config file can be updated by a second kishu instance / configparser.
    """
    assert 'PLANNER' in Config.config

    # Set a string field.
    assert 'string_field' not in Config.config['PLANNER']
    Config.set('PLANNER', 'string_field', '42')
    assert Config.get('PLANNER', 'string_field', '0') == '42'

    # Second parser which will update the config file.
    second_parser = configparser.ConfigParser()
    second_parser.read(Config.CONFIG_PATH)

    # For preventing race conditions related to st_mtime_ns.
    time.sleep(0.01)

    # Second parser updates the config file.
    assert 'PLANNER' in second_parser
    assert 'string_field' in second_parser['PLANNER']
    second_parser['PLANNER']['string_field'] = '2119'
    with open(Config.CONFIG_PATH, 'w') as configfile2:
        second_parser.write(configfile2)

    # The field should be updated correctly.
    assert Config.get('PLANNER', 'string_field', '0') == '2119'


def test_skip_reread():
    """
        Tests accessing a config value when the config file has not been updated
        skips the file read.
    """
    assert 'PLANNER' in Config.config

    Config.set('PLANNER', 'test_field1', 1)
    Config.set('PLANNER', 'test_field2', 2)

    assert Config.get('PLANNER', 'test_field1', 0) == 1
    first_read_time = os.path.getatime(Config.CONFIG_PATH)
    assert Config.get('PLANNER', 'test_field2', 0) == 2
    second_read_time = os.path.getatime(Config.CONFIG_PATH)

    # The second call to config.get does not result in the config file being read again.
    assert first_read_time == second_read_time


def test_manual_bad_write():
    # For preventing race conditions related to st_mtime_ns.
    time.sleep(0.01)

    # Manually write garbage into the config file.
    with open(Config.CONFIG_PATH, "wb") as configfile:
        configfile.write(b"abcdefg")
        configfile.flush()
        os.fsync(configfile.fileno())

    # Assert reading the config file fails.
    with pytest.raises(configparser.MissingSectionHeaderError):
        assert Config.get('PROFILER', 'excluded_modules', []) == ["a"]


def test_set_and_get_nonexistant_category():
    assert 'ABCDEFG' not in Config.config

    # Check that accessing a nonexistant category throws an error.
    with pytest.raises(KeyError):
        Config.get('ABCDEFG', 'abcdefg', 1)

    # Check that writing to a nonexistant category throws an error.
    with pytest.raises(KeyError):
        Config.set('ABCDEFG', 'abcdefg', 1)


def test_backward_compatibility():
    print(Config.CONFIG_PATH)
    # The config file should not exist before the first get call.
    assert not os.path.isfile(Config.CONFIG_PATH)

    # Remove a category, then create a config file without the category.
    Config.DEFAULT_CATEGORIES.remove("OPTIMIZER")
    _ = Config.get('PLANNER', 'nonexistant_field', "1")

    # Querying for the new category should create it.
    assert Config.get('OPTIMIZER', 'network_bandwidth', 1.0) == 1.0
    assert "OPTIMIZER" in Config.config
