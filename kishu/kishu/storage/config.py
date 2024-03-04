import ast
import configparser
import os

from typing import Any

from kishu.exceptions import MissingConfigCategoryError
from kishu.storage.path import KishuPath


class Config:
    CONFIG_PATH = os.path.join(KishuPath.kishu_directory(), "config.ini")
    config = configparser.ConfigParser()
    last_read_time = -1.0

    # Default config categories.
    DEFAULT_CATEGORIES = ['CLI', 'COMMIT_GRAPH', 'JUPYTERINT', 'OPTIMIZER', 'PLANNER', 'PROFILER']

    @staticmethod
    def _create_config_file() -> None:
        """
            Creates a config file with default parameters.
        """
        for category in Config.DEFAULT_CATEGORIES:
            Config.config[category] = {}

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

        last_modify_time = os.stat(Config.CONFIG_PATH).st_mtime_ns

        # Only re-read the config file if it was modified since last read.
        # Note: the granularity of st_mtime_ns depends on the system (e.g., 1ms) and can result in very
        # recent updates being missed.
        if Config.last_read_time < last_modify_time:
            Config.config.read(Config.CONFIG_PATH)

            # Update the last read time.
            Config.last_read_time = last_modify_time

    @staticmethod
    def _write_config_file() -> None:
        """
            Writes the config file.
        """
        with open(Config.CONFIG_PATH, 'w') as configfile:
            Config.config.write(configfile)
            configfile.flush()
            os.fsync(configfile.fileno())

    @staticmethod
    def get(config_category: str, config_entry: str, default: Any) -> Any:
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
            if config_category in Config.DEFAULT_CATEGORIES:
                # If the category is intended to exist but not in the config file (e.g., file
                # from older version of Kishu), create the category
                Config.config[config_category] = {}
                Config._write_config_file()
            else:
                raise MissingConfigCategoryError(config_category)

        # Lists can't be cast directly to the type of the default and need to be parsed.
        if isinstance(default, list) and config_entry in Config.config[config_category]:
            return ast.literal_eval(Config.config[config_category][config_entry])

        return type(default)(Config.config[config_category].get(config_entry, default))

    @staticmethod
    def set(config_category: str, config_entry: str, config_value: Any) -> None:
        """
            Sets the value of an entry in the config file.

            @param config_category: category of the entry, e.g., PLANNER.
            @param config_entry: entry to get value of, e.g., migration_speed_bps.
            @param config_value: Value to set the entry to.
        """
        Config._read_config_file()

        if config_category not in Config.config:
            if config_category in Config.DEFAULT_CATEGORIES:
                # If the category is intended to exist but not in the config file (e.g., file
                # from older version of Kishu), create the category
                Config.config[config_category] = {}
            else:
                raise MissingConfigCategoryError(config_category)

        Config.config[config_category][config_entry] = str(config_value)

        Config._write_config_file()
