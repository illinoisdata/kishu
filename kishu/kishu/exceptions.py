"""
Raised by state
"""


class TypeNotSupportedError(Exception):
    def __init__(self, type_name, var_name, var_value):
        super().__init__(f'{type_name} not yet supported ({var_name, var_value}).')


"""
Raised by notebook_id
"""


class MissingNotebookMetadataError(Exception):
    def __init__(self):
        super().__init__("Missing Kishu metadata in the notebook.")


class NotNotebookPathOrKey(Exception):
    def __init__(self, s: str):
        super().__init__(f"\"{s}\" is neither a notebook path nor a Kishu notebook key.")


"""
Raised by branch
"""


class BranchNotFoundError(Exception):
    def __init__(self, branch_name):
        super().__init__(f"The provided branch '{branch_name}' does not exist.")


class BranchConflictError(Exception):
    def __init__(self, message):
        super().__init__(message)


"""
Raised by jupyterint
"""


class JupyterConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class MissingConnectionInfoError(JupyterConnectionError):
    def __init__(self):
        super().__init__("Missing kernel connection information.")


class KernelNotAliveError(JupyterConnectionError):
    def __init__(self):
        super().__init__("Kernel is not alive.")


class StartChannelError(JupyterConnectionError):
    def __init__(self):
        super().__init__("Failed to start a channel to kernel.")


class NoChannelError(JupyterConnectionError):
    def __init__(self):
        super().__init__("No channel is connected.")


class NoFormattedCellsError(Exception):
    def __init__(self, commit_id=None):
        message = "No formatted cells"
        if commit_id:
            message += f" for commitID: {commit_id}"
        super().__init__(message)


class NoExecutedCellsError(Exception):
    def __init__(self, commit_id=None):
        message = "No executed cells"
        if commit_id:
            message += f" for commitID: {commit_id}"
        super().__init__(message)


class PostWithoutPreError(Exception):
    def __init__(self):
        super().__init__("Called post_run_cell without calling pre_run_cell")


"""
Raised by planner
"""


class MissingHistoryError(Exception):
    def __init__(self):
        super().__init__("Missing cell execution history.")


"""
Raised by commit
"""


class MissingCommitEntryError(Exception):
    def __init__(self, commit_id):
        super().__init__(f"Missing commit entry for commit ID: {commit_id}.")
