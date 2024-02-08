import configparser
import os
import pytest
from kishu.exceptions import MissingConfigCategoryError


def test_initialize_config_get_default(tmp_path_config: type):
    # The config file should not exist before the first get call.
    assert not os.path.isfile(tmp_path_config.CONFIG_PATH)

    # Assert default categories exist.
    for category in tmp_path_config.DEFAULT_CATEGORIES:
        assert category in tmp_path_config.config

    # Check that the field has not been previously set.
    assert 'nonexistant_field' not in tmp_path_config.config['PLANNER']

    # When the field doesn't exist, the default value is returned.
    assert tmp_path_config.get(tmp_path_config.DEFAULT_CATEGORIES[0], 'nonexistant_field', "1") == "1"


def test_set_and_get_new_fields(tmp_path_config: type):
    assert 'PLANNER' in tmp_path_config.config

    # Test with string.
    assert 'string_field' not in tmp_path_config.config['PLANNER']
    tmp_path_config.set('PLANNER', 'string_field', '42')
    assert tmp_path_config.get('PLANNER', 'string_field', '0') == '42'

    # Test with int.
    assert 'int_field' not in tmp_path_config.config['PLANNER']
    tmp_path_config.set('PLANNER', 'int_field', 42)
    assert tmp_path_config.get('PLANNER', 'int_field', 0) == 42


def test_set_and_get_update_fields(tmp_path_config: type):
    assert 'PROFILER' in tmp_path_config.config

    # Check that the field has not been previously set.
    assert 'excluded_modules' not in tmp_path_config.config['PROFILER']
    tmp_path_config.set('PROFILER', 'excluded_modules', ["a"])
    assert tmp_path_config.get('PROFILER', 'excluded_modules', []) == ["a"]

    # Check that the field is updated.
    tmp_path_config.set('PROFILER', 'excluded_modules', ["1", "2"])
    assert tmp_path_config.get('PROFILER', 'excluded_modules', []) == ["1", "2"]


def test_concurrent_update_field(tmp_path_config: type):
    """
        Tests the config file can be updated by a second kishu instance / configparser.
    """
    assert 'PLANNER' in tmp_path_config.config

    # Set a string field.
    assert 'string_field' not in tmp_path_config.config['PLANNER']
    tmp_path_config.set('PLANNER', 'string_field', '42')
    assert tmp_path_config.get('PLANNER', 'string_field', '0') == '42'

    # Second parser which will update the config file.
    second_parser = configparser.ConfigParser()
    second_parser.read(tmp_path_config.CONFIG_PATH)

    # Second parser updates the config file.
    assert 'PLANNER' in second_parser
    assert 'string_field' in second_parser['PLANNER']
    second_parser['PLANNER']['string_field'] = '2119'
    with open(tmp_path_config.CONFIG_PATH, 'w') as configfile2:
        second_parser.write(configfile2)

    # The field should be updated correctly.
    assert tmp_path_config.get('PLANNER', 'string_field', '0') == '2119'


def test_skip_reread(tmp_path_config: type):
    """
        Tests accessing a config value when the config file has not been updated
        skips the file read.
    """
    assert 'PLANNER' in tmp_path_config.config

    tmp_path_config.set('PLANNER', 'test_field1', 1)
    tmp_path_config.set('PLANNER', 'test_field2', 2)

    assert tmp_path_config.get('PLANNER', 'test_field1', 0) == 1
    first_read_time = os.path.getatime(tmp_path_config.CONFIG_PATH)
    assert tmp_path_config.get('PLANNER', 'test_field2', 0) == 2
    second_read_time = os.path.getatime(tmp_path_config.CONFIG_PATH)

    # The second call to config.get does not result in the config file being read again.
    assert first_read_time == second_read_time


def test_manual_bad_write(tmp_path_config: type):
    # Manually write garbage into the config file.
    with open(tmp_path_config.CONFIG_PATH, "wb") as config_file:
        config_file.write(b"abcdefg")

    # Assert reading the config file fails.
    with pytest.raises(configparser.MissingSectionHeaderError):
        assert tmp_path_config.get('PROFILER', 'excluded_modules', []) == ["a"]


def test_set_and_get_nonexistant_category(tmp_path_config: type):
    assert 'ABCDEFG' not in tmp_path_config.config

    # Check that accessing a nonexistant caegory throws an error.
    with pytest.raises(MissingConfigCategoryError):
        tmp_path_config.get('ABCDEFG', 'abcdefg', 1)

    # Check that writing to a nonexistant caegory throws an error.
    with pytest.raises(MissingConfigCategoryError):
        tmp_path_config.set('ABCDEFG', 'abcdefg', 1)
