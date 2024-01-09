from typing import Dict, Set


class VariableVersionTracker:

    def __init__(self, current_variable_version: Dict[str, str]) -> None:
        # key: variable name, value: commit_id
        self.current_variables_version = current_variable_version

    def update_variable_version(self, new_commit_id: str, changed_vars: Set[str], delete_vars: Set[str]) -> None:
        for var_name in delete_vars:
            if var_name in self.current_variables_version:
                del self.current_variables_version[var_name]
        for var_name in changed_vars:
            self.current_variables_version[var_name] = new_commit_id

    def get_variable_versions(self) -> Dict[str, str]:
        return self.current_variables_version

    def set_current(self, new_variable_version: Dict[str, str]) -> None:
        self.current_variables_version = new_variable_version
