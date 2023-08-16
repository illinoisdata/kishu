

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import jupyter_client

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


@dataclass
class HistoryCommit:
    oid: str
    parent_oid: str
    timestamp: str
    branch_id: str
    parent_branch_id: str


@dataclass
class SelectedHistoryCommit:
    oid: str
    # version: str  # ???
    content: str
    exec_num: str


@dataclass
class SelectedHistoryVariable:
    variable_name: str
    # version: str  # ???
    state: str  # string?


@dataclass
class SelectedHistory:
    oid: str
    # parent_oid: str
    timestamp: str
    exec_cell: str
    # branch_id: str
    # parent_branch_id: str
    # cells: List[SelectedHistoryCommit]  # TODO: not yet recorded.
    variables: List[SelectedHistoryVariable]


FESelectedHistory = SelectedHistory


@dataclass
class FEInitializeResult:
    histories: List[HistoryCommit]


class KishuCommand:

    @staticmethod
    def log(notebook_id: str, commit_id: str) -> LogResult:
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
    def checkout(notebook_id: str, commit_id: str) -> CheckoutResult:
        connection = KishuForJupyter.retrieve_connection(notebook_id)
        if connection is None:
            return CheckoutResult(
                status="missing_kernel_connection"
            )
        cf = jupyter_client.find_connection_file(connection.kernel_id)
        km = jupyter_client.BlockingKernelClient(connection_file=cf)
        km.load_connection_file()
        km.start_channels()
        km.wait_for_ready()
        if km.is_alive():
            reply = km.execute(
                f"_kishu.checkout('{commit_id}')",
                reply=True,
                store_history=False,  # Do not increment cell count.
            )
            km.stop_channels()
            return CheckoutResult(
                status=reply["content"]["status"]
            )
        else:
            return CheckoutResult(
                status="failed_connection"
            )

    @staticmethod
    def fe_initialize(notebook_id: str) -> FEInitializeResult:
        store = KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
        graph = store.list_all_history()
        exec_infos = KishuCommand._find_exec_info(notebook_id, graph)

        # Collects list of HistoryCommits.
        histories = []
        for node in graph:
            exec_info = exec_infos.get(node.commit_id, UnitExecution())
            cell_exec_info = cast(CellExecInfo, exec_info)  # TODO: avoid this cast.
            histories.append(HistoryCommit(
                oid=node.commit_id,
                parent_oid=node.parent_id,
                timestamp=KishuCommand._to_datetime(cell_exec_info.end_time_ms),
                branch_id="",  # To be set in _toposort_history.
                parent_branch_id="",  # To be set in _toposort_history.
            ))
        histories = KishuCommand._toposort_history(histories)

        # Combines everything.
        return FEInitializeResult(
            histories=histories,
        )

    @staticmethod
    def fe_history(notebook_id: str, commit_id: str) -> FESelectedHistory:
        current_cell_exec_info = KishuCommand._find_cell_exec_info(notebook_id, commit_id)
        return KishuCommand._join_selected_history(notebook_id, commit_id, current_cell_exec_info)

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
    def _join_selected_history(
        notebook_id: str,
        commit_id: str,
        cell_exec_info: CellExecInfo,
    ) -> SelectedHistory:
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
            SelectedHistoryVariable(
                variable_name=key,
                state=str(value),
            ) for key, value in commit_variables.items()
        ]

        # Builds SelectedHistory.
        return SelectedHistory(
            oid=commit_id,
            timestamp=KishuCommand._to_datetime(cell_exec_info.end_time_ms),
            exec_cell=cell_exec_info.code_block if cell_exec_info.code_block else "",
            variables=variables,
        )

    @staticmethod
    def _toposort_history(histories: List[HistoryCommit]) -> List[HistoryCommit]:
        refs: Dict[str, List[int]] = {}
        for idx, history in enumerate(histories):
            if history.parent_oid == "":
                continue
            if history.parent_oid not in refs:
                refs[history.parent_oid] = []
            refs[history.parent_oid].append(idx)

        sorted_histories = []
        free_commit_idxs = [
            idx for idx, history in enumerate(histories)
            if history.parent_oid == ""
        ]
        new_branch_id = 1
        for free_commit_idx in free_commit_idxs:
            # Next history is next in topological order.
            history = histories[free_commit_idx]
            if history.branch_id == "":
                assert history.parent_oid == ""
                history.branch_id = str(new_branch_id)
                history.parent_branch_id = str(-1)
                new_branch_id += 1
            sorted_histories.append(history)

            # Assigns children branch IDs.
            child_idxs = refs.get(history.oid, [])
            for child_idx in child_idxs[1:]:
                child_history = histories[child_idx]
                child_history.branch_id = str(new_branch_id)
                child_history.parent_branch_id = hi story.branch_id
                new_branch_id += 1
                free_commit_idxs.append(child_idx)
            if len(child_idxs) > 0:
                # Add first child last to continue this branch after branching out.
                histories[child_idxs[0]].branch_id = history.branch_id
                histories[child_idxs[0]].parent_branch_id = history.branch_id
                free_commit_idxs.append(child_idxs[0])
        return sorted_histories

    @staticmethod
    def _to_datetime(epoch_time_ms: Optional[int]) -> str:
        return (
            "" if epoch_time_ms is None
            else datetime.datetime.fromtimestamp(epoch_time_ms / 1000).strftime("%Y-%m-%d,%H:%M:%S")
        )

