import sqlite3
from pathlib import Path
from typing import Dict, List, Set

VARIABLE_VERSION_TABLE = "variable_version"
COMMIT_VARIABLE_VERSION_TABLE = "commit_variable"


class VariableVersion:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        cur.execute(
            f"create table if not exists {VARIABLE_VERSION_TABLE}"
            f" (var_name text, var_commit_id text, primary key (var_name, var_commit_id))"
        )
        cur.execute(f"create index if not exists var_name_index " f"on {VARIABLE_VERSION_TABLE} (var_name)")

        # every variable for every commit will be stored in the commit_variable table
        cur.execute(
            f"create table if not exists {COMMIT_VARIABLE_VERSION_TABLE} "
            f"(commit_id text, var_name text, var_commit_id text, primary key (var_name, commit_id))"
        )
        cur.execute(f"create index if not exists commit_id_index on " f"{COMMIT_VARIABLE_VERSION_TABLE} (commit_id)")

        con.commit()

    def store_variable_version_table(self, var_names: Set[str], commit_id: str):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        for var_name in var_names:
            cur.execute(f"insert into {VARIABLE_VERSION_TABLE} values (?, ?)", (var_name, commit_id))
        con.commit()

    def store_commit_variable_version_table(self, commit_id: str, commit_variable_version_map: Dict[str, str]):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        values_to_insert = [(commit_id, key, value) for key, value in commit_variable_version_map.items()]
        cur.executemany(f"insert into {COMMIT_VARIABLE_VERSION_TABLE} values (?, ?, ?)", values_to_insert)
        con.commit()

    def get_variable_version_by_commit_id(self, commit_id: str) -> Dict[str, str]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select var_name, var_commit_id from {COMMIT_VARIABLE_VERSION_TABLE} where commit_id = ?", (commit_id,))
        result = {var_name: var_commit_id for var_name, var_commit_id in cur}
        con.commit()
        return result

    def get_commit_ids_by_variable_name(self, variable_name: str) -> List[str]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select var_commit_id from {VARIABLE_VERSION_TABLE} where var_name = ?", (variable_name,))
        result = [item[0] for item in cur]
        con.commit()
        return result
