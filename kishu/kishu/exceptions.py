from pathlib import Path
from typing import Any, Optional

"""
Raised by notebook_id
"""


class MissingNotebookMetadataError(Exception):
    def __init__(self):
        super().__init__("Missing Kishu metadata in the notebook.")


"""
Raised by path
"""


class NotPathError(Exception):
    def __init__(self, obj: Any):
        super().__init__(f'"{obj}" is not a Path object.')


class NotebookNotFoundError(Exception):
    def __init__(self, path: Path):
        super().__init__(f"{path} does not exist.")


class PathIsNotNotebookError(Exception):
    def __init__(self, path: Path):
        super().__init__(f"{path} is not a notebook.")


class KishuNotInitializedError(Exception):
    def __init__(self, path: Path):
        super().__init__(f"Kishu for notebook {path} has not been initialized.")


"""
Raised by branch
"""


class BranchNotFoundError(Exception):
    def __init__(self, branch_name: str):
        super().__init__(f"The provided branch '{branch_name}' does not exist.")


class BranchConflictError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


"""
Raised by checkpoint
"""


class CommitIdNotExistError(Exception):
    def __init__(self, commit_id: str):
        super().__init__(f"Commit ID '{commit_id}' does not exist.")


"""
Raised by tag
"""


class TagNotFoundError(Exception):
    def __init__(self, tag_name: str):
        super().__init__(f"The provided tag '{tag_name}' does not exist.")


"""
Raised by jupyterint
"""


class JupyterConnectionError(Exception):
    def __init__(self, message: str):
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
    def __init__(self, commit_id: Optional[str] = None):
        message = "No formatted cells"
        if commit_id:
            message += f" for commitID: {commit_id}"
        super().__init__(message)


class NoExecutedCellsError(Exception):
    def __init__(self, commit_id: Optional[str] = None):
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
    def __init__(self, commit_id: str):
        super().__init__(f"Missing commit entry for commit ID: {commit_id}.")
