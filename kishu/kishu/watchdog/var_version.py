from typing import Dict
from kishu.storage.checkpoint_io import store_variable_version_table, store_commit_variable_version_table, \
    get_variable_version_by_commit_id, get_commit_ids_by_variable_name


class VariableVersionTracker:
    def __init__(self, dbfile: str, current_commit_id: str):
        # key: variable name, value: commit_id
        self.current_variables_version: Dict[str, str] = {}
        self.dbfile = dbfile

        # get the head commit_id and construct the variable_commitID_map by reading the variable_version table
        # if head does not exist, then the current_variables_version map is empty
        if current_commit_id is not "":
            self.current_variables_version = VariableVersion.get_variable_version(current_commit_id, self.dbfile)

    def update_variable_version(self, new_commit_id: str, changed_vars: set[str], delete_vars: set[str]):
        # step 1: update the variable_version table
        store_variable_version_table(self.dbfile, changed_vars | delete_vars, new_commit_id)

        # step 2: update the variable version for the current commit in memory
        for var_name in delete_vars:
            if var_name in self.current_variables_version:
                del self.current_variables_version[var_name]
        for var_name in changed_vars:
            self.current_variables_version[var_name] = new_commit_id

        # step 3: update the commit_variable table
        store_commit_variable_version_table(self.dbfile, new_commit_id, self.current_variables_version)

    def restore_variable_version(self, commit_id: str):
        self.current_variables_version = VariableVersion.get_variable_version(commit_id, self.dbfile)


class VariableVersion:
    @staticmethod
    def get_variable_changing_commits(variable_name: str, dbfile: str) -> list[str]:
        """
        param: variable_name: the name of the variable
        return: a list of commit_id that changes the variable
        """
        return get_commit_ids_by_variable_name(dbfile, variable_name)

    @staticmethod
    def get_variable_version(commit_id: str, dbfile: str) -> Dict[str, str]:
        return get_variable_version_by_commit_id(dbfile, commit_id)

