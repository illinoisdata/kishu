import sqlite3

from typing import Dict, List

from kishu.storage.path import KishuPath

VARIABLE_VERSION_TABLE = 'variable_version'

COMMIT_VARIABLE_VERSION_TABLE = 'commit_variable'


class VariableVersion:
    def __init__(self, notebook_id: str):
        self.database_path = KishuPath.database_path(notebook_id)

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        cur.execute(
            f'create table if not exists {VARIABLE_VERSION_TABLE} (var_name text, var_commit_id text, primary key (var_name, var_commit_id))')
        cur.execute(f'create index if not exists var_name_index on {VARIABLE_VERSION_TABLE} (var_name)')

        # every variable for every commit will be stored in the commit_variable table
        cur.execute(
            f'create table if not exists {COMMIT_VARIABLE_VERSION_TABLE} (commit_id text, var_name text, var_commit_id text, primary key (var_name, commit_id))')
        cur.execute(f'create index if not exists commit_id_index on {COMMIT_VARIABLE_VERSION_TABLE} (commit_id)')

        con.commit()

    def store_variable_version_table(self,var_names: set[str], commit_id: str):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        for var_name in var_names:
            cur.execute(
                "insert into {} values (?, ?)".format(VARIABLE_VERSION_TABLE),
                (var_name, commit_id)
            )
        con.commit()

    def store_commit_variable_version_table(self, commit_id: str, commit_variable_version_map: Dict[str, str]):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        for key, value in commit_variable_version_map.items():
            cur.execute(
                "insert into {} values (?, ?, ?)".format(COMMIT_VARIABLE_VERSION_TABLE),
                (commit_id, key, value)
            )
        con.commit()

    def get_variable_version_by_commit_id(self, commit_id: str) -> Dict[str, str]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            "select var_name, var_commit_id from {} where commit_id = ?".format(COMMIT_VARIABLE_VERSION_TABLE),
            (commit_id,)
        )
        res = cur.fetchall()
        result = {}
        for var_name, var_commit_id in res:
            result[var_name] = var_commit_id
        con.commit()
        return result

    def get_commit_ids_by_variable_name(self, variable_name: str) -> List[str]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        print("var_name", variable_name)
        print("select var_commit_id from {} where var_name = ?".format(VARIABLE_VERSION_TABLE),
              (variable_name))
        cur.execute(
            "select var_commit_id from {} where var_name = ?".format(VARIABLE_VERSION_TABLE),
            (variable_name,)
        )
        res = cur.fetchall()
        result = []
        for var_commit_id in res:
            result.append(var_commit_id)
        con.commit()
        return result

