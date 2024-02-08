import configparser
import os
import time

from typing import Any

from kishu.exceptions import MissingConfigCategoryError
from kishu.storage.path import KishuPath


class Config:
    CONFIG_PATH = os.path.join(KishuPath.kishu_directory(), "config.ini")
    config = configparser.ConfigParser()
    last_get_config_time = -1
    last_set_config_time = 0

    @staticmethod
    def _create_config_file() -> None:
        """
            Creates a config file with default parameters.
        """
        Config.config['CLI'] = {}
        Config.config['COMMIT_GRAPH'] = {}
        Config.config['JUPYTERINT'] = {}
        Config.config['PLANNER'] = {}
        Config.config['PROFILER'] = {}
        with open(Config.CONFIG_PATH, 'w') as configfile:
            Config.config.write(configfile)

    @staticmethod
    def _read_config_file() -> None:
        """
            Reads the config file.
        """
        # Create the config file if it doesn't exist.
        if not os.path.isfile(Config.CONFIG_PATH):
            Config._create_config_file()

        # Only re-read the config file if it was modified since last read
        if Config.last_get_config_time < Config.last_set_config_time:
            Config.config.read(Config.CONFIG_PATH)

        # Update the last read time.
        Config.last_get_config_time = time.time()

    @staticmethod
    def get_config_entry(config_category: str, config_entry: str, default: Any) -> Any:
        """
            Gets the value of an entry from the config file.

            @param config_category: category of the entry, e.g., PLANNER.
            @param config_entry: entry to get value of, e.g., migration_speed_bps.
            @param default: default value if the entry is not set. The return value,
                if retrieved from the config file, will be converted to the same type
                as this parameter.
        """
        Config._read_config_file()

        if config_category not in Config.config:
            raise MissingConfigCategoryError(config_category)

        return type(default)(Config.config[config_category].get(config_entry, default))

    @staticmethod
    def set_config_entry(config_category: str, config_entry: str, config_value: Any) -> None:
        """
            Sets the value of an entry in the config file.

            @param config_category: category of the entry, e.g., PLANNER.
            @param config_entry: entry to get value of, e.g., migration_speed_bps.
            @param config_value: Value to set the entry to.
        """
        Config._read_config_file()

        if config_category not in Config.config:
            raise MissingConfigCategoryError(config_category)

        Config.config[config_category][config_entry] = config_value

        with open(Config.CONFIG_PATH, 'w') as configfile:
            Config.config.write(configfile)

        # Update the last write time.
        Config.last_set_config_time = os.path.getmtime(Config.CONFIG_PATH)
