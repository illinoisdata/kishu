from __future__ import annotations
import datetime
import heapq
import json
import jupyter_client
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

from kishu.branch import BranchRow, HeadBranch, KishuBranch
from kishu.commit_graph import CommitInfo, KishuCommitGraph
from kishu.jupyterint2 import CellExecInfo, KishuForJupyter
from kishu.plan import UnitExecution
from kishu.resources import KishuResource


@dataclass
class CommitSummary:
    commit_id: str
    parent_id: str
    code_block: Optional[str]
    runtime_ms: Optional[int]


@dataclass
class LogResult:
    commit_graph: List[CommitSummary]


@dataclass
class LogAllResult:
    commit_graph: List[CommitSummary]


@dataclass
class StatusResult:
    commit_info: CommitInfo
    cell_exec_info: CellExecInfo


@dataclass
class CheckoutResult:
    status: str
    message: str


@dataclass
class BranchResult:
    status: str
    branch_name: Optional[str] = None
    commit_id: Optional[str] = None
    head: Optional[HeadBranch] = None


@dataclass
class HistoricalCommit:
    oid: str
    parent_oid: str
    timestamp: str
    branch_id: str
    parent_branch_id: str
    other_branch_ids: List[str]


@dataclass
class SelectedCommitCell:
    cell_type: str
    content: str
    output: Optional[str]
    exec_num: Optional[str]
    # oid: str  # ???
    # version: str  # ???


@dataclass
class SelectedCommitVariable:
    variable_name: str
    state: str
    type: str
    children: List[SelectedCommitVariable]
    size: Optional[str]
    # version: str  # ???


@dataclass
class SelectedCommit:
    oid: str
    parent_oid: str
    timestamp: str
    cells: List[SelectedCommitCell]
    variables: List[SelectedCommitVariable]
    # branch_id: str
    # parent_branch_id: str
    # exec_cell: str  # ???
    # tag: str  # ???


FESelectedCommit = SelectedCommit


@dataclass
class FEInitializeResult:
    commits: List[HistoricalCommit]
    head: Optional[HeadBranch]


class KishuCommand:

    @staticmethod
    def log(notebook_id: str, commit_id: Optional[str] = None) -> LogResult:
        if commit_id is None:
            head = KishuBranch.get_head(notebook_id)
            commit_id = head.commit_id

        if commit_id is None:
            return LogResult([])

        store = KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
        graph = store.list_history(commit_id)
        exec_infos = KishuCommand._find_exec_info(notebook_id, graph)
        return LogResult(KishuCommand._join_commit_summary(graph, exec_infos))

    @staticmethod
    def log_all(notebook_id: str) -> LogAllResult:
        store = KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
        graph = store.list_all_history()
        exec_infos = KishuCommand._find_exec_info(notebook_id, graph)
        return LogAllResult(KishuCommand._join_commit_summary(graph, exec_infos))

    @staticmethod
    def status(notebook_id: str, commit_id: str) -> StatusResult:
        commit_info = next(
            KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
                            .iter_history(commit_id)
        )
        cell_exec_info = KishuCommand._find_cell_exec_info(notebook_id, commit_id)
        return StatusResult(
            commit_info=commit_info,
            cell_exec_info=cell_exec_info
        )

    @staticmethod
    def checkout(notebook_id: str, branch_or_commit_id: str) -> CheckoutResult:
        connection = KishuForJupyter.retrieve_connection(notebook_id)
        if connection is None:
            return CheckoutResult(
                status="error",
                message="Missing kernel connection information",
            )

        # Find connection file.
        try:
            cf = jupyter_client.find_connection_file(connection.kernel_id)
        except OSError:
            return CheckoutResult(
                status="error",
                message="Kernel is not alive",
            )

        # Connect to kernel.
        km = jupyter_client.BlockingKernelClient(connection_file=cf)
        km.load_connection_file()
        km.start_channels()
        km.wait_for_ready()
        if km.is_alive():
            reply = km.execute(
                f"_kishu.checkout('{branch_or_commit_id}')",
                reply=True,
                silent=True,
                # store_history=False,  # Do not increment cell count.
            )
            km.stop_channels()
            if reply["content"]["status"] == "ok":
                return CheckoutResult(
                    status="ok",
                    message=f"Checkout {branch_or_commit_id}",
                )
            elif reply["content"]["status"] == "error":
                # print("\n".join(reply["content"]["traceback"]))
                ename = reply["content"]["ename"]
                evalue = reply["content"]["evalue"]
                return CheckoutResult(
                    status="error",
                    message=f"{ename}: {evalue}",
                )
            return CheckoutResult(
                status=reply["content"]["status"],
                message=json.dumps(reply["content"]),
            )
        else:
            return CheckoutResult(
                status="error",
                message="Failed to connect to kernel",
            )

    @staticmethod
    def branch(notebook_id: str, branch_name: str, commit_id: Optional[str]) -> BranchResult:
        head = KishuBranch.get_head(notebook_id)

        if commit_id is None:
            # If no commit ID, create branch pointing to the commit ID at HEAD.
            head = KishuBranch.update_head(notebook_id, branch_name=branch_name)
            commit_id = head.commit_id
        elif branch_name == head.branch_name and commit_id != head.commit_id:
            # Moving head branch somewhere else.
            head = KishuBranch.update_head(notebook_id, is_detach=True)
            print(f"detaching {head}")

        # Fail to determine commit ID, possibly because a commit does not exist.
        if commit_id is None:
            return BranchResult(status="no_commit")

        # Now add this branch.
        KishuBranch.upsert_branch(notebook_id, branch_name, commit_id)

        return BranchResult(
            status="ok",
            branch_name=branch_name,
            commit_id=commit_id,
            head=head,
        )

    @staticmethod
    def fe_commit_graph(notebook_id: str) -> FEInitializeResult:
        store = KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
        graph = store.list_all_history()
        exec_infos = KishuCommand._find_exec_info(notebook_id, graph)

        # Collects list of HistoricalCommits.
        commits = []
        for node in graph:
            exec_info = exec_infos.get(node.commit_id, UnitExecution())
            cell_exec_info = cast(CellExecInfo, exec_info)  # TODO: avoid this cast.
            commits.append(HistoricalCommit(
                oid=node.commit_id,
                parent_oid=node.parent_id,
                timestamp=KishuCommand._to_datetime(cell_exec_info.end_time_ms),
                branch_id="",  # To be set in _toposort_commits.
                parent_branch_id="",  # To be set in _toposort_commits.
                other_branch_ids=[],
            ))
        commits = KishuCommand._toposort_commits(commits)

        # Retreives and applies branch names.
        head = KishuBranch.get_head(notebook_id)
        branches = KishuBranch.list_branch(notebook_id)
        commits = KishuCommand._rebranch_commit(commits, branches)

        # Combines everything.
        return FEInitializeResult(
            commits=commits,
            head=head,
        )

    @staticmethod
    def fe_commit(notebook_id: str, commit_id: str, vardepth: int) -> FESelectedCommit:
        commit_info = next(
            KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
                            .iter_history(commit_id)
        )
        current_cell_exec_info = KishuCommand._find_cell_exec_info(notebook_id, commit_id)
        return KishuCommand._join_selected_commit(
            notebook_id,
            commit_id,
            commit_info,
            current_cell_exec_info,
            vardepth=vardepth,
        )

    """Helpers"""

    @staticmethod
    def _find_exec_info(notebook_id: str, graph: List[CommitInfo]) -> Dict[str, UnitExecution]:
        exec_infos = UnitExecution.get_commits(
            KishuResource.checkpoint_path(notebook_id),
            [node.commit_id for node in graph]
        )
        return exec_infos

    @staticmethod
    def _find_cell_exec_info(notebook_id: str, commit_id: str) -> CellExecInfo:
        # TODO: Pull CellExecInfo logic out of jupyterint2 to avoid this cast.
        return cast(
            CellExecInfo,
            UnitExecution.get_from_db(
                KishuResource.checkpoint_path(notebook_id),
                commit_id,
            )
        )

    @staticmethod
    def _join_commit_summary(
        graph: List[CommitInfo],
        exec_infos: Dict[str, UnitExecution],
    ) -> List[CommitSummary]:
        summaries = []
        for node in graph:
            exec_info = exec_infos.get(node.commit_id, UnitExecution())
            summaries.append(CommitSummary(
                commit_id=node.commit_id,
                parent_id=node.parent_id,
                code_block=exec_info.code_block,
                runtime_ms=exec_info.runtime_ms,
            ))
        return summaries

    @staticmethod
    def _join_selected_commit(
        notebook_id: str,
        commit_id: str,
        commit_info: CommitInfo,
        cell_exec_info: CellExecInfo,
        vardepth: int,
    ) -> SelectedCommit:
        # Restores variables.
        commit_variables: Dict[str, Any] = {}
        restore_plan = cell_exec_info._restore_plan
        if restore_plan is not None:
            restore_plan.run(
                commit_variables,
                KishuResource.checkpoint_path(notebook_id),
                commit_id
            )
        variables = [
            KishuCommand._make_selected_variable(key, value, vardepth=vardepth)
            for key, value in commit_variables.items()
        ]

        # Compile list of cells.
        cells: List[SelectedCommitCell] = []
        if cell_exec_info.executed_cells is not None:
            for executed_cell in cell_exec_info.executed_cells:
                cells.append(SelectedCommitCell(
                    cell_type=executed_cell.cell_type,
                    content=executed_cell.source,
                    output=executed_cell.output,
                    exec_num=str(executed_cell.execution_count),
                ))

        # Builds SelectedCommit.
        return SelectedCommit(
            oid=commit_id,
            parent_oid=commit_info.parent_id,
            timestamp=KishuCommand._to_datetime(cell_exec_info.end_time_ms),
            variables=variables,
            cells=cells,
        )

    @staticmethod
    def _toposort_commits(commits: List[HistoricalCommit]) -> List[HistoricalCommit]:
        refs: Dict[str, List[int]] = {}
        for idx, commit in enumerate(commits):
            if commit.parent_oid == "":
                continue
            if commit.parent_oid not in refs:
                refs[commit.parent_oid] = []
            refs[commit.parent_oid].append(idx)

        sorted_commits = []
        free_commit_idxs = [
            (0.0, commit.timestamp, idx) for idx, commit in enumerate(commits)
            if commit.parent_oid == ""
        ]
        heapq.heapify(free_commit_idxs)
        new_branch_id = 1
        it = 0.0
        while len(free_commit_idxs) > 0:
            # Next commit is next in topological order.
            _, _, free_commit_idx = heapq.heappop(free_commit_idxs)
            commit = commits[free_commit_idx]
            it += 1

            # If branch not assigned, this commit is in a new branch.
            if commit.branch_id == "":
                assert commit.parent_oid == ""
                commit.branch_id = f"tmp_{new_branch_id}"
                commit.parent_branch_id = "-1"
                new_branch_id += 1
            sorted_commits.append(commit)

            # Assigns children branch IDs.
            child_idxs = refs.get(commit.oid, [])
            for child_idx in child_idxs[1:]:
                child_commit = commits[child_idx]
                child_commit.branch_id = f"tmp_{new_branch_id}"
                child_commit.parent_branch_id = commit.branch_id
                new_branch_id += 1
                heapq.heappush(free_commit_idxs, (it, child_commit.timestamp, child_idx))
            if len(child_idxs) > 0:
                # Add first child last to continue this branch after branching out.
                child_commit = commits[child_idxs[0]]
                child_commit.branch_id = commit.branch_id
                child_commit.parent_branch_id = commit.branch_id
                heapq.heappush(free_commit_idxs, (it + 0.5, child_commit.timestamp, child_idxs[0]))
        return sorted_commits

    @staticmethod
    def _rebranch_commit(
        commits: List[HistoricalCommit],
        branches: List[BranchRow],
    ) -> List[HistoricalCommit]:
        # Each of new branches points to one commit, creating an aliasing mapping.
        commit_to_branch_name = {
            branch.commit_id: branch.branch_name
            for branch in branches
        }

        # Find mapping between current branch names to new branch names base on commit.
        # Assume: commits are sorted, so the head commit of a branch is the last commit in the list.
        head_commits_by_old_branch = {commit.branch_id: commit.oid for commit in commits}
        old_to_new_branch_name = {
            old_branch: commit_to_branch_name[commit_id]
            for old_branch, commit_id in head_commits_by_old_branch.items() if commit_id in commit_to_branch_name
        }

        # List other branch names that will not show up.
        selected_branch_names = {branch_name for _, branch_name in old_to_new_branch_name.items()}
        commit_to_other_branch_names: Dict[str, List[str]] = {
            commit_id: [] for commit_id in commit_to_branch_name
        }
        for branch in branches:
            commit_to_other_branch_names[branch.commit_id].append(branch.branch_name)
        for commit_id in commit_to_other_branch_names:
            other_branch_names = filter(
                lambda branch_name: branch_name not in selected_branch_names,
                commit_to_other_branch_names[commit_id]
            )
            commit_to_other_branch_names[commit_id] = sorted(other_branch_names)    

        # Edit branches in commits.
        for commit in commits:
            # Now relabel every branch names.
            if commit.branch_id in old_to_new_branch_name:
                commit.branch_id = old_to_new_branch_name[commit.branch_id]
            if commit.parent_branch_id in old_to_new_branch_name:
                commit.parent_branch_id = old_to_new_branch_name[commit.parent_branch_id]

            # Insert other branch names.
            if commit.oid in commit_to_other_branch_names:
                commit.other_branch_ids = commit_to_other_branch_names[commit.oid]
        return commits

    @staticmethod
    def _to_datetime(epoch_time_ms: Optional[int]) -> str:
        return (
            "" if epoch_time_ms is None
            else datetime.datetime.fromtimestamp(epoch_time_ms / 1000).strftime("%Y-%m-%d,%H:%M:%S")
        )

    @staticmethod
    def _make_selected_variable(key: str, value: Any, vardepth: int = 1) -> SelectedCommitVariable:
        return SelectedCommitVariable(
            variable_name=key,
            state=str(value),
            type=str(type(value).__name__),
            children=KishuCommand._recurse_variable(value, vardepth=vardepth),
            size=KishuCommand._size_or_none(value),
        )

    @staticmethod
    def _recurse_variable(value: Any, vardepth: int) -> List[SelectedCommitVariable]:
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
