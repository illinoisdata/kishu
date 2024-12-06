import ast
import configparser
import os
import sqlite3
from pathlib import Path
from typing import Any

import dill

from kishu.storage.path import KishuPath

PERSISTENT_CONFIG_TABLE = "persistent_config"


def str_to_bool(s: str) -> bool:
    if s.lower() in {"true", "1", "yes"}:
        return True
    elif s.lower() in {"false", "0", "no"}:
        return False
    else:
        raise ValueError(f"Cannot convert '{s}' to boolean.")


class Config:
    CONFIG_PATH = KishuPath.config_path()
    config = configparser.ConfigParser()
    last_read_time = -1.0

    # Default config categories.
    DEFAULT_CATEGORIES = ["CLI", "COMMIT_GRAPH", "IDGRAPH", "JUPYTERINT", "OPTIMIZER", "PLANNER", "PROFILER"]

    @staticmethod
    def _create_config_file() -> None:
        """
        Creates a config file with default parameters.
        """
        for category in Config.DEFAULT_CATEGORIES:
            Config.config[category] = {}

        with open(Config.CONFIG_PATH, "w") as configfile:
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

            # If the config category is supposed to exists but doesn't exist (e.g., config file created
            # in earlier version of kishu), create it.
            for config_category in Config.DEFAULT_CATEGORIES:
                if config_category not in Config.config:
                    Config.config[config_category] = {}

            # Update the last read time.
            Config.last_read_time = last_modify_time

    @staticmethod
    def _write_config_file() -> None:
        """
        Writes the config file.
        """
        with open(Config.CONFIG_PATH, "w") as configfile:
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

        # Lists can't be cast directly to the type of the default and need to be parsed.
        if isinstance(default, list) and config_entry in Config.config[config_category]:
            return ast.literal_eval(Config.config[config_category][config_entry])

        # Direct casting of booleans (e.g., bool("False") == True) doesn't work; use a mapping.
        elif isinstance(default, bool) and config_entry in Config.config[config_category]:
            return str_to_bool(Config.config[config_category][config_entry])

        else:
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

        Config.config[config_category][config_entry] = str(config_value)

        Config._write_config_file()


class PersistentConfig:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        """
        Creates the table for storing persistent configs. Persistent configs are initialized
        upon session start (e.g., incremental_store) and cannot be mutated.
        """
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"""create table if not exists {PERSISTENT_CONFIG_TABLE} """
            """(config_category text, config_entry text, config_value blob, primary key(config_category, config_entry))"""
        )
        con.commit()

    def drop_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"drop table if exists {PERSISTENT_CONFIG_TABLE}")
        con.commit()

    def _set_from_config(self, config_category: str, config_entry: str, config_value: Any) -> None:
        config_value = Config.get(config_category, config_entry, config_value)
        config_value_dill = dill.dumps(config_value)
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"insert into {PERSISTENT_CONFIG_TABLE} values (?, ?, ?)",
            (config_category, config_entry, memoryview(config_value_dill)),
        )
        con.commit()

    def get(self, config_category: str, config_entry: str, default: Any) -> Any:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"select config_value from {PERSISTENT_CONFIG_TABLE} where config_category = ? and config_entry = ?",
            (
                config_category,
                config_entry,
            ),
        )
        res: tuple = cur.fetchone()
        if not res:
            self._set_from_config(config_category, config_entry, default)
            return self.get(config_category, config_entry, default)
        result = dill.loads(res[0])
        con.commit()
        return result
