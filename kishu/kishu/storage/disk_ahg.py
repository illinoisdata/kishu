"""
Sqlite interface for storing the AHG.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, List

from kishu.jupyter.namespace import Namespace
from kishu.planning.profiler import profile_variable_size
from kishu.storage.commit_graph import CommitId
from kishu.storage.config import Config

AHG_VARIABLE_SNAPSHOT_TABLE = "ahg_variable_snapshot"
AHG_CELL_EXECUTION_TABLE = "ahg_cell_execution"
AHG_CE_INPUT_TABLE = "ahg_ce_input"
AHG_CE_OUTPUT_TABLE = "ahg_ce_output"
AHG_ACTIVE_VSES_TABLE = "ahg_active_vses"


# Aliases
VariableName = FrozenSet[str]
CellExecutionNumber = int


@dataclass(frozen=True)
class CellExecution:
    """
    A cell execution (object) corresponds to a cell execution (action, i.e. press play) in the notebook session.

    @param cell_num: The nth cell execution of the current session.
    @param cell: Raw cell code.
    @param cell_runtime_s: Cell runtime in seconds.
    """

    cell_num: CellExecutionNumber
    cell: str
    cell_runtime_s: float = 1.0


@dataclass(frozen=True)
class VariableSnapshot:
    """
    A variable snapshot in the dependency graph corresponds to a version of a variable.
    I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have 3 corresponding
    variable snapshots.
        @param name: one or more variable names sharing references forming a connected component.
        @param version: time of creation or update to the corresponding variable name.
        @param deleted: whether this VS is created for the deletion of a variable, i.e., 'del x'.
        @param size: estimated size of the VariableSnapshot in bytes.
    """

    name: VariableName
    version: int
    deleted: bool = False
    size: float = 1.0

    @staticmethod
    def select_names_from_update(user_ns: Namespace, version: int, name: VariableName) -> VariableSnapshot:
        always_recompute = Config.get("OPTIMIZER", "always_recompute", False)
        always_migrate = Config.get("OPTIMIZER", "always_migrate", False)
        size = 1.0
        if (not always_recompute) and (not always_migrate):
            size = profile_variable_size([user_ns[var] for var in name])
        return VariableSnapshot(
            name=name,
            version=version,
            deleted=False,
            size=size,
        )

    def versioned_name(self) -> str:
        return repr(self.version) + "," + ",".join(sorted(list(self.name)))

    @staticmethod
    def from_db_row(versioned_name: str, deleted: bool, size: float) -> VariableSnapshot:
        split_str = versioned_name.split(",")
        version = int(split_str[0])
        name = frozenset(split_str[1:])
        return VariableSnapshot(name, version, deleted, size)


@dataclass
class AHGUpdateResult:
    """
    New items from an AHG update to persist to database.
    """

    commit_id: CommitId
    accessed_vss: List[VariableSnapshot]
    output_vss: List[VariableSnapshot]
    newest_ce: CellExecution
    active_vss: List[VariableSnapshot]


class KishuDiskAHG:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"create table if not exists {AHG_VARIABLE_SNAPSHOT_TABLE} "
            "(versioned_name text primary key, deleted bool, size float)"
        )
        cur.execute(
            f"create table if not exists {AHG_CELL_EXECUTION_TABLE} "
            "(cell_num int primary key, cell text, cell_runtime_s float)"
        )
        cur.execute(
            f"create table if not exists {AHG_CE_INPUT_TABLE} "
            "(cell_num int, versioned_name text, primary key (cell_num, versioned_name))"
        )
        cur.execute(
            f"create table if not exists {AHG_CE_OUTPUT_TABLE} "
            "(cell_num int, versioned_name text, primary key (cell_num, versioned_name))"
        )
        cur.execute(f"create table if not exists {AHG_ACTIVE_VSES_TABLE} (commit_id text, versioned_name text)")

        con.commit()

    def drop_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"drop table if exists {AHG_VARIABLE_SNAPSHOT_TABLE}")
        cur.execute(f"drop table if exists {AHG_CELL_EXECUTION_TABLE}")
        cur.execute(f"drop table if exists {AHG_CE_INPUT_TABLE}")
        cur.execute(f"drop table if exists {AHG_CE_OUTPUT_TABLE}")
        cur.execute(f"drop table if exists {AHG_ACTIVE_VSES_TABLE}")
        con.commit()

    def store_update_results(self, update_result: AHGUpdateResult):
        # Unpack items
        commit_id = update_result.commit_id
        accessed_vss = update_result.accessed_vss
        output_vss = update_result.output_vss
        newest_ce = update_result.newest_ce
        active_vss = update_result.active_vss

        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Store each output VS.
        for vs in output_vss:
            cur.execute(
                f"insert into {AHG_VARIABLE_SNAPSHOT_TABLE} values (?, ?, ?)",
                (vs.versioned_name(), vs.deleted, vs.size),
            )

        # Store the newest CE.
        cur.execute(
            f"insert into {AHG_CELL_EXECUTION_TABLE} values (?, ?, ?)",
            (newest_ce.cell_num, newest_ce.cell, newest_ce.cell_runtime_s),
        )

        # Store each VS to CE edge.
        for vs in accessed_vss:
            cur.execute(
                f"insert into {AHG_CE_INPUT_TABLE} values (?, ?)",
                (newest_ce.cell_num, vs.versioned_name()),
            )

        # Store each CE to VS edge.
        for vs in output_vss:
            cur.execute(
                f"insert into {AHG_CE_OUTPUT_TABLE} values (?, ?)",
                (newest_ce.cell_num, vs.versioned_name()),
            )

        # Store active VSes.
        for vs in active_vss:
            cur.execute(
                f"insert into {AHG_ACTIVE_VSES_TABLE} values (?, ?)",
                (commit_id, vs.versioned_name()),
            )

        con.commit()

    def get_all_variable_snapshots(self) -> List[VariableSnapshot]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select * from {AHG_VARIABLE_SNAPSHOT_TABLE}")
        res: List = cur.fetchall()
        return [VariableSnapshot.from_db_row(versioned_name, deleted, size) for versioned_name, deleted, size in res]

    def get_all_cell_executions(self) -> List[CellExecution]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select * from {AHG_CELL_EXECUTION_TABLE}")
        res: List = cur.fetchall()
        return [CellExecution(cell_num, cell, cell_runtime_s) for cell_num, cell, cell_runtime_s in res]

    def get_vs_by_versioned_names(self, versioned_names: List[str]) -> List[VariableSnapshot]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"select * from {AHG_VARIABLE_SNAPSHOT_TABLE} WHERE versioned_name IN (%s)" % ",".join("?" * len(versioned_names)),
            versioned_names,
        )
        res: List = cur.fetchall()
        return [VariableSnapshot.from_db_row(versioned_name, deleted, size) for versioned_name, deleted, size in res]

    def get_ce_by_cell_num(self, cell_num: CellExecutionNumber) -> CellExecution:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select * from {AHG_CELL_EXECUTION_TABLE} where cell_num = ?", (cell_num,))
        res: tuple = cur.fetchone()
        if not res:
            raise ValueError(f"The CellExecution for cell number = {cell_num} was not found")
        return CellExecution(res[0], res[1], res[2])

    def get_active_vses(self, commit_id: CommitId) -> List[VariableSnapshot]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select versioned_name from {AHG_ACTIVE_VSES_TABLE} where commit_id = ?", (commit_id,))
        res: List = cur.fetchall()
        return self.get_vs_by_versioned_names([i[0] for i in res])

    def get_vs_input_ce(self, vs: VariableSnapshot) -> CellExecution:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select cell_num from {AHG_CE_OUTPUT_TABLE} where versioned_name = ?", (vs.versioned_name(),))
        res: tuple = cur.fetchone()
        if not res:
            raise ValueError(f"The (unique) CE creating VS with version = {vs.version} and name = {vs.name} not found")
        return self.get_ce_by_cell_num(res[0])

    def get_ce_input_vses(self, ce: CellExecution) -> List[VariableSnapshot]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select versioned_name from {AHG_CE_INPUT_TABLE} where cell_num = ?", (ce.cell_num,))
        res: List = cur.fetchall()
        return self.get_vs_by_versioned_names([i[0] for i in res])

    def get_ce_output_vses(self, ce: CellExecution) -> List[VariableSnapshot]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select versioned_name from {AHG_CE_OUTPUT_TABLE} where cell_num = ?", (ce.cell_num,))
        res: List = cur.fetchall()
        return self.get_vs_by_versioned_names([i[0] for i in res])
