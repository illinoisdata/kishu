from __future__ import annotations

import datetime
import json

from dataclasses import asdict, dataclass, is_dataclass
from dataclasses_json import dataclass_json
from pathlib import Path
from typing import Any, Dict, List, Optional

from kishu.exceptions import (
    BranchNotFoundError,
    BranchConflictError,
)
from kishu.diff import DiffHunk, KishuDiff
from kishu.exceptions import NoExecutedCellsError, NoFormattedCellsError
from kishu.jupyterint import (
    JupyterCommandResult,
    JupyterConnection,
    KishuForJupyter,
    KishuSession,
)
from kishu.jupyter.namespace import Namespace
from kishu.jupyter.runtime import JupyterRuntimeEnv
from kishu.notebook_id import NotebookId
from kishu.storage.branch import BranchRow, HeadBranch, KishuBranch
from kishu.storage.commit import CommitEntry, FormattedCell, KishuCommit
from kishu.storage.commit_graph import CommitNodeInfo, KishuCommitGraph
from kishu.storage.path import KishuPath
from kishu.storage.tag import KishuTag, TagRow


"""
Printing dataclasses
"""


class DataclassJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        try:
            return super().default(o)
        except TypeError:
            return o.__repr__()


def into_json(data):
    return json.dumps(data, cls=DataclassJSONEncoder, indent=2)


"""
KishuCommand
"""


@dataclass_json
@dataclass
class ListResult:
    sessions: List[KishuSession]


@dataclass_json
@dataclass
class InitResult:
    status: str
    message: str
    notebook_id: Optional[NotebookId]  # Field must be filled if status is OK

    @staticmethod
    def wrap(result: JupyterCommandResult, nb_id: Optional[NotebookId]) -> InitResult:
        return InitResult(
            status=result.status,
            message=result.message,
            notebook_id=nb_id
        )


@dataclass_json
@dataclass
class DetachResult:
    status: str
    message: str

    @staticmethod
    def wrap(result: JupyterCommandResult) -> DetachResult:
        return DetachResult(
            status=result.status,
            message=result.message,
        )


@dataclass
class CommitSummary:
    commit_id: str
    parent_id: str
    message: str
    timestamp: str
    raw_cell: Optional[str]
    runtime_s: Optional[float]
    branches: List[str]
    tags: List[str]


@dataclass_json
@dataclass
class LogResult:
    commit_graph: List[CommitSummary]
    head: HeadBranch


@dataclass
class LogAllResult:
    commit_graph: List[CommitSummary]
    head: HeadBranch


@dataclass
class StatusResult:
    commit_node_info: CommitNodeInfo
    commit_entry: CommitEntry


CheckoutResult = JupyterCommandResult
CommitResult = JupyterCommandResult


@dataclass_json
@dataclass
class BranchResult:
    status: str
    branch_name: Optional[str] = None
    commit_id: Optional[str] = None
    head: Optional[HeadBranch] = None


@dataclass_json
@dataclass
class DeleteBranchResult:
    status: str
    message: str


@dataclass_json
@dataclass
class RenameBranchResult:
    status: str
    branch_name: str
    message: str


@dataclass
class TagResult:
    status: str
    tag_name: Optional[str] = None
    commit_id: Optional[str] = None
    message: Optional[str] = None


@dataclass
class FECommit:
    oid: str
    parent_oid: str
    timestamp: str
    branches: List[str]
    tags: List[str]
    code_version: int
    var_version: int


@dataclass
class FESelectedCommitCell:
    cell_type: str
    content: str
    output: Optional[str]
    exec_num: Optional[str]


@dataclass
class FESelectedCommitVariable:
    variable_name: str
    state: str
    type: str
    children: List[FESelectedCommitVariable]
    size: Optional[str]


@dataclass
class FESelectedCommit:
    commit: FECommit
    executed_cells: List[str]
    cells: List[FESelectedCommitCell]
    variables: List[FESelectedCommitVariable]


@dataclass
class FEInitializeResult:
    commits: List[FECommit]
    head: HeadBranch


@dataclass
class FECodeDiffResult:
    notebook_cells_diff: List[DiffHunk]
    executed_cells_diff: List[DiffHunk]


class KishuCommand:

    @staticmethod
    def list(list_all: bool = False) -> ListResult:
        sessions = KishuForJupyter.kishu_sessions()

        # Filter out non-alive Kishu sessions if ask for.
        if not list_all:
            sessions = list(filter(lambda session: session.is_alive, sessions))

        # Sort by notebook ID.
        sessions = sorted(sessions, key=lambda session: session.notebook_key)
        return ListResult(sessions=sessions)

    @staticmethod
    def init(notebook_path_str: str) -> InitResult:
        notebook_path = Path(notebook_path_str)
        try:
            kernel_id = JupyterRuntimeEnv.kernel_id_from_notebook(notebook_path)
        except FileNotFoundError as e:
            return InitResult(
                notebook_id=None,
                status="error",
                message=f"{type(e).__name__}: {str(e)}",
            )
        init_result = JupyterConnection(kernel_id).execute_one_command(
            pre_command=f"from kishu import init_kishu; init_kishu(\"{notebook_path.resolve()}\")",
            command="str(_kishu)",
        )
        notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path_str)
        return InitResult.wrap(init_result, NotebookId(notebook_key, notebook_path, kernel_id))

    @staticmethod
    def detach(notebook_path_str: str) -> DetachResult:
        notebook_path = Path(notebook_path_str)
        try:
            kernel_id = JupyterRuntimeEnv.kernel_id_from_notebook(notebook_path)
        except FileNotFoundError as e:
            return DetachResult(
                status="error",
                message=f"{type(e).__name__}: {str(e)}",
            )
        return DetachResult.wrap(JupyterConnection(kernel_id).execute_one_command(
            pre_command=f"from kishu import detach_kishu; detach_kishu(\"{notebook_path.resolve()}\")",
            command=f"\"Successfully detatched notebook at {notebook_path.resolve()}\"",
        ))

    @staticmethod
    def log(notebook_id: str, commit_id: Optional[str] = None) -> LogResult:
        if commit_id is None:
            head = KishuBranch.get_head(notebook_id)
            commit_id = head.commit_id

        if commit_id is None:
            return LogResult(commit_graph=[], head=KishuBranch.get_head(notebook_id))

        commit_id = KishuForJupyter.disambiguate_commit(notebook_id, commit_id)
        store = KishuCommitGraph.new_on_file(KishuPath.commit_graph_directory(notebook_id))
        graph = store.list_history(commit_id)
        return LogResult(
            commit_graph=KishuCommand._decorate_graph(notebook_id, graph),
            head=KishuBranch.get_head(notebook_id),
        )

    @staticmethod
    def log_all(notebook_id: str) -> LogAllResult:
        store = KishuCommitGraph.new_on_file(KishuPath.commit_graph_directory(notebook_id))
        graph = store.list_all_history()
        return LogAllResult(
            commit_graph=KishuCommand._decorate_graph(notebook_id, graph),
            head=KishuBranch.get_head(notebook_id),
        )

    @staticmethod
    def status(notebook_id: str, commit_id: str) -> StatusResult:
        commit_id = KishuForJupyter.disambiguate_commit(notebook_id, commit_id)
        commit_node_info = next(
            KishuCommitGraph.new_on_file(KishuPath.commit_graph_directory(notebook_id))
                            .iter_history(commit_id)
        )
        commit_entry = KishuCommand._find_commit_entry(notebook_id, commit_id)
        return StatusResult(
            commit_node_info=commit_node_info,
            commit_entry=commit_entry
        )

    @staticmethod
    def commit(notebook_id: str, message: Optional[str] = None) -> CommitResult:
        return JupyterConnection.from_notebook_key(notebook_id).execute_one_command(
            "_kishu.commit()" if message is None else f"_kishu.commit(message=\"{message}\")",
        )

    @staticmethod
    def checkout(
        notebook_id: str,
        branch_or_commit_id: str,
        skip_notebook: bool = False,
    ) -> CheckoutResult:
        return JupyterConnection.from_notebook_key(notebook_id).execute_one_command(
            f"_kishu.checkout('{branch_or_commit_id}', skip_notebook={skip_notebook})",
        )

    @staticmethod
    def branch(
        notebook_id: str,
        branch_name: str,
        commit_id: Optional[str],
        do_commit: bool = False,
    ) -> BranchResult:
        head = KishuBranch.get_head(notebook_id)

        if commit_id is None:
            # If no commit ID, create branch pointing to the commit ID at HEAD.
            head = KishuBranch.update_head(notebook_id, branch_name=branch_name)
            commit_id = head.commit_id
        elif branch_name == head.branch_name and commit_id != head.commit_id:
            # Moving head branch somewhere else.
            head = KishuBranch.update_head(notebook_id, is_detach=True)
            print(f"detaching {head}")

        # Fail to determine commit ID, possibly because no commit does not exist.
        if commit_id is None:
            return BranchResult(status="no_commit")

        # Now add this branch.
        commit_id = KishuForJupyter.disambiguate_commit(notebook_id, commit_id)
        KishuBranch.upsert_branch(notebook_id, branch_name, commit_id)

        # Create new commit for this branch action.
        if do_commit:
            commit_id = KishuCommand._checkout_and_commit_after_branch(notebook_id, branch_name, commit_id)

        return BranchResult(
            status="ok",
            branch_name=branch_name,
            commit_id=commit_id,
            head=head,
        )

    @staticmethod
    def delete_branch(
        notebook_id: str,
        branch_name: str,
    ) -> DeleteBranchResult:
        try:
            KishuBranch.delete_branch(notebook_id, branch_name)
            return DeleteBranchResult(
                status="ok",
                message=f"Branch {branch_name} deleted.",
            )
        except (BranchConflictError, BranchNotFoundError) as e:
            return DeleteBranchResult(
                status="error",
                message=str(e),
            )

    @staticmethod
    def rename_branch(
        notebook_id: str,
        old_name: str,
        new_name: str,
    ) -> RenameBranchResult:
        try:
            KishuBranch.rename_branch(notebook_id, old_name, new_name)
            return RenameBranchResult(
                status="ok",
                branch_name=new_name,
                message=f"Branch renamed from {old_name} to {new_name}.",
            )
        except (BranchNotFoundError, BranchConflictError) as e:
            return RenameBranchResult(
                status="error",
                branch_name="",
                message=str(e),
            )

    @staticmethod
    def tag(
        notebook_id: str,
        tag_name: str,
        commit_id: Optional[str],
        message: str,
    ) -> TagResult:
        # Attempt to fill in omitted commit ID.
        if commit_id is None:
            # Try creating tag pointing to the commit ID at HEAD.
            head = KishuBranch.get_head(notebook_id)
            commit_id = head.commit_id

        # Fail to determine commit ID, possibly because a commit does not exist.
        if commit_id is None:
            return TagResult(status="no_commit")

        # Now add this tag.
        commit_id = KishuForJupyter.disambiguate_commit(notebook_id, commit_id)
        tag = TagRow(tag_name=tag_name, commit_id=commit_id, message=message)
        KishuTag.upsert_tag(notebook_id, tag)
        return TagResult(
            status="ok",
            tag_name=tag_name,
            commit_id=commit_id,
            message=message,
        )

    @staticmethod
    def fe_commit_graph(notebook_id: str) -> FEInitializeResult:
        store = KishuCommitGraph.new_on_file(KishuPath.commit_graph_directory(notebook_id))
        graph = store.list_all_history()
        graph_commit_ids = [node.commit_id for node in graph]
        commit_entries = KishuCommand._find_commit_entries(notebook_id, graph_commit_ids)

        # Collects list of FECommits.
        commits = []
        for node in graph:
            commit_entry = commit_entries.get(node.commit_id, CommitEntry())
            commits.append(FECommit(
                oid=node.commit_id,
                parent_oid=node.parent_id,
                timestamp=KishuCommand._to_datetime(commit_entry.timestamp),
                branches=[],  # To be set in _branch_commit.
                tags=[],  # To be set in _tag_commit.
                code_version=commit_entry.code_version,
                var_version=commit_entry.var_version,
            ))

        # Retreives and joins branches.
        head = KishuBranch.get_head(notebook_id)
        branches = KishuBranch.list_branch(notebook_id)
        commits = KishuCommand._branch_commit(commits, branches)

        # Joins with tag list.
        tags = KishuTag.list_tag(notebook_id)
        commits = KishuCommand._tag_commit(commits, tags)

        # Sort commits by timestamp.
        commits = sorted(commits, key=lambda commit: commit.timestamp)

        # Combines everything.
        return FEInitializeResult(
            commits=commits,
            head=head,
        )

    @staticmethod
    def fe_commit(notebook_id: str, commit_id: str, vardepth: int) -> FESelectedCommit:
        commit_id = KishuForJupyter.disambiguate_commit(notebook_id, commit_id)
        commit_node_info = next(
            KishuCommitGraph.new_on_file(KishuPath.commit_graph_directory(notebook_id))
                            .iter_history(commit_id)
        )
        current_commit_entry = KishuCommand._find_commit_entry(notebook_id, commit_id)
        branches = KishuBranch.branches_for_commit(notebook_id, commit_id)
        tags = KishuTag.tags_for_commit(notebook_id, commit_id)
        return KishuCommand._join_selected_commit(
            notebook_id,
            commit_id,
            commit_node_info,
            current_commit_entry,
            branches,
            tags,
            vardepth=vardepth,
        )

    @staticmethod
    def fe_commit_diff(notebook_id: str, from_commit_id: str, to_commit_id: str) -> FECodeDiffResult:
        to_cells, to_executed_cells = KishuCommand._retrieve_all_cells(notebook_id, to_commit_id)
        from_cells, from_executed_cells = KishuCommand._retrieve_all_cells(notebook_id, from_commit_id)
        cell_diff = KishuDiff.diff_cells(from_cells, to_cells)
        executed_cell_diff = KishuDiff.diff_cells(from_executed_cells, to_executed_cells)
        return FECodeDiffResult(cell_diff, executed_cell_diff)

    """Helpers"""

    @staticmethod
    def _decorate_graph(notebook_id: str, graph: List[CommitNodeInfo]) -> List[CommitSummary]:
        graph_commit_ids = [node.commit_id for node in graph]
        commit_entries = KishuCommand._find_commit_entries(notebook_id, graph_commit_ids)
        branch_by_commit = KishuBranch.branches_for_many_commits(notebook_id, graph_commit_ids)
        tag_by_commit = KishuTag.tags_for_many_commits(notebook_id, graph_commit_ids)
        commits = KishuCommand._join_commit_summary(
            graph,
            commit_entries,
            branch_by_commit,
            tag_by_commit,
        )
        commits = sorted(commits, key=lambda commit: commit.timestamp)
        return commits

    @staticmethod
    def _find_commit_entries(notebook_id: str, commit_ids: List[str]) -> Dict[str, CommitEntry]:
        kishu_commit = KishuCommit(KishuPath.database_path(notebook_id))
        return kishu_commit.get_log_items(commit_ids)

    @staticmethod
    def _find_commit_entry(notebook_id: str, commit_id: str) -> CommitEntry:
        kishu_commit = KishuCommit(KishuPath.database_path(notebook_id))
        return kishu_commit.get_log_item(commit_id)

    @staticmethod
    def _join_commit_summary(
        graph: List[CommitNodeInfo],
        commit_entries: Dict[str, CommitEntry],
        branch_by_commit: Dict[str, List[BranchRow]],
        tag_by_commit: Dict[str, List[TagRow]],
    ) -> List[CommitSummary]:
        summaries = []
        for node in graph:
            commit_entry = commit_entries.get(node.commit_id, CommitEntry())
            branch_names = [
                branch.branch_name for branch in branch_by_commit.get(node.commit_id, [])
            ]
            tag_names = [tag.tag_name for tag in tag_by_commit.get(node.commit_id, [])]
            summaries.append(CommitSummary(
                commit_id=node.commit_id,
                parent_id=node.parent_id,
                message=commit_entry.message,
                timestamp=KishuCommand._to_datetime(commit_entry.timestamp),
                raw_cell=commit_entry.raw_cell,
                runtime_s=commit_entry.runtime_s,
                branches=branch_names,
                tags=tag_names,
            ))
        return summaries

    @staticmethod
    def _join_selected_commit(
        notebook_id: str,
        commit_id: str,
        commit_node_info: CommitNodeInfo,
        commit_entry: CommitEntry,
        branches: List[BranchRow],
        tags: List[TagRow],
        vardepth: int,
    ) -> FESelectedCommit:
        # Restores variables.
        commit_variables = Namespace({})
        restore_plan = commit_entry.restore_plan
        if restore_plan is not None:
            restore_plan.run(
                commit_variables,
                KishuPath.database_path(notebook_id),
                commit_id
            )
        variables = [
            KishuCommand._make_selected_variable(key, value, vardepth=vardepth)
            for key, value in commit_variables.to_dict().items()
        ]

        # Compile list of executed cells.
        executed_cells = [] if commit_entry.executed_cells is None else commit_entry.executed_cells

        # Compile list of cells.
        cells: List[FESelectedCommitCell] = []
        if commit_entry.formatted_cells is not None:
            for formatted_cell in commit_entry.formatted_cells:
                cells.append(FESelectedCommitCell(
                    cell_type=formatted_cell.cell_type,
                    content=formatted_cell.source,
                    output=formatted_cell.output,
                    exec_num=KishuCommand._str_or_none(formatted_cell.execution_count),
                ))

        # Summarize branches and tags
        branch_names = [branch.branch_name for branch in branches]
        tag_names = [tag.tag_name for tag in tags]

        # Builds FESelectedCommit.
        commit_summary = FECommit(
            oid=commit_id,
            parent_oid=commit_node_info.parent_id,
            timestamp=KishuCommand._to_datetime(commit_entry.timestamp),
            branches=branch_names,
            tags=tag_names,
            code_version=commit_entry.code_version,
            var_version=commit_entry.var_version,
        )
        return FESelectedCommit(
            commit=commit_summary,
            executed_cells=executed_cells,
            variables=variables,
            cells=cells,
        )

    @staticmethod
    def _branch_commit(
        commits: List[FECommit],
        branches: List[BranchRow],
    ) -> List[FECommit]:
        # Group branch names by commit ID
        commit_to_branch: Dict[str, List[str]] = {}
        for branch in branches:
            if branch.commit_id not in commit_to_branch:
                commit_to_branch[branch.commit_id] = []
            commit_to_branch[branch.commit_id].append(branch.branch_name)

        # Join branch names to commits.
        for commit in commits:
            commit.branches.extend(commit_to_branch.get(commit.oid, []))
        return commits

    @staticmethod
    def _tag_commit(
        commits: List[FECommit],
        tags: List[TagRow],
    ) -> List[FECommit]:
        # Group tag names by commit ID
        commit_to_tag: Dict[str, List[str]] = {}
        for tag in tags:
            if tag.commit_id not in commit_to_tag:
                commit_to_tag[tag.commit_id] = []
            commit_to_tag[tag.commit_id].append(tag.tag_name)

        # Join tag names to commits.
        for commit in commits:
            commit.tags.extend(commit_to_tag.get(commit.oid, []))
        return commits

    @staticmethod
    def _checkout_and_commit_after_branch(notebook_id: str, branch_name: str, commit_id: str) -> str:
        # Checkout to move HEAD to branch.
        checkout_result = KishuCommand.checkout(notebook_id, branch_name)
        if checkout_result.status != "ok":
            print(
                f"Checkout failed after branch (message: {checkout_result.message}). "
                "Skipping commit this branch action."
            )
            return commit_id

        # Commit branch action.
        commit_result = KishuCommand.commit(
            notebook_id,
            f"Set {branch_name} branch to {commit_id} commit.",
        )
        if commit_result.status != "ok":
            print(
                f"Commit failed after branch (message: {commit_result.message}). "
                "Skipping commit this branch action."
            )
            return commit_id

        # Return new commit ID
        commit_id = commit_result.message
        return commit_id

    @staticmethod
    def _to_datetime(epoch_time: Optional[float]) -> str:
        return (
            "" if epoch_time is None
            else datetime.datetime
                         .fromtimestamp(epoch_time)
                         .strftime("%Y-%m-%d %H:%M:%S.%f")
        )

    @staticmethod
    def _make_selected_variable(key: str, value: Any, vardepth: int = 1) -> FESelectedCommitVariable:
        return FESelectedCommitVariable(
            variable_name=key,
            state=str(value),
            type=str(type(value).__name__),
            children=KishuCommand._recurse_variable(value, vardepth=vardepth),
            size=KishuCommand._size_or_none(value),
        )

    @staticmethod
    def _recurse_variable(value: Any, vardepth: int) -> List[FESelectedCommitVariable]:
        if vardepth <= 0:
            return []

        # TODO: Maybe we should iterate on other internal members too.
        children = []
        if hasattr(value, "__dict__"):
            for sub_key, sub_value in value.__dict__.items():
                children.append(KishuCommand._make_selected_variable(
                    key=sub_key,
                    value=sub_value,
                    vardepth=vardepth-1,
                ))
        return children

    @staticmethod
    def _size_or_none(value: Any) -> Optional[str]:
        if hasattr(value, "shape"):
            return str(value.shape)
        elif hasattr(value, '__len__'):
            try:
                return str(len(value))
            except TypeError:
                # Some type implements __len__ but not qualify for len().
                return None
        return None

    @staticmethod
    def _str_or_none(value: Optional[Any]) -> Optional[str]:
        return None if value is None else str(value)

    @staticmethod
    def _get_cells_as_strings(formated_cells: List[FormattedCell]) -> List[str]:
        return [cell.source for cell in formated_cells]

    @staticmethod
    def _retrieve_all_cells(notebook_id: str, commit_id: str):
        commit_entry = KishuCommand._find_commit_entry(notebook_id, commit_id)
        formatted_cells = commit_entry.formatted_cells
        if formatted_cells is None:
            raise NoFormattedCellsError(commit_id)
        executed_cells = commit_entry.executed_cells
        if executed_cells is None:
            raise NoExecutedCellsError(commit_id)
        cells = KishuCommand._get_cells_as_strings(formatted_cells)
        return cells, executed_cells
