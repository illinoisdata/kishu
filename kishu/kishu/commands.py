from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, cast

from kishu.resources import KishuResource
from kishu.commit_graph import CommitInfo, KishuCommitGraph
from kishu.plan import UnitExecution
from kishu.jupyterint2 import CellExecInfo


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


class KishuCommand:

    @staticmethod
    def log(notebook_id: str, commit_id: str) -> LogResult:
        store = KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
        graph = store.list_history(commit_id)
        return LogResult(KishuCommand._augment_from_checkpoint(notebook_id, graph))

    @staticmethod
    def log_all(notebook_id: str) -> LogAllResult:
        store = KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
        graph = store.list_all_history()
        return LogAllResult(KishuCommand._augment_from_checkpoint(notebook_id, graph))

    @staticmethod
    def status(notebook_id: str, commit_id: str) -> StatusResult:
        commit_info = next(
            KishuCommitGraph.new_on_file(KishuResource.commit_graph_directory(notebook_id))
                            .iter_history(commit_id)
        )

        # TODO: Pull CellExecInfo logic out of jupyterint2 to avoid this cast.
        cell_exec_info: CellExecInfo = cast(
            CellExecInfo,
            UnitExecution.get_from_db(
                KishuResource.checkpoint_path(notebook_id),
                commit_id,
            )
        )
        return StatusResult(
            commit_info=commit_info,
            cell_exec_info=cell_exec_info
        )

    @staticmethod
    def _augment_from_checkpoint(notebook_id: str, graph: List[CommitInfo]) -> List[CommitSummary]:
        exec_infos = UnitExecution.get_commits(
            KishuResource.checkpoint_path(notebook_id),
            [node.commit_id for node in graph]
        )
        return KishuCommand._join(graph, exec_infos)

    @staticmethod
    def _join(graph: List[CommitInfo], exec_infos: Dict[str, UnitExecution]) -> List[CommitSummary]:
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
