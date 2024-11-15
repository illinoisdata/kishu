"""
Sqlite interface for storing the AHG.
"""

import sqlite3
from pathlib import Path
from typing import List, Set, Tuple

import dill as pickle

from kishu.planning.ahg import AHG, AHGUpdateResult, CellExecution, VariableSnapshot, VersionedName

AHG_VARIABLE_SNAPSHOT_TABLE = "ahg_variable_snapshot"
AHG_CELL_EXECUTION_TABLE = "ahg_cell_execution"
AHG_CE_INPUT_TABLE = "ahg_ce_input"
AHG_CE_OUTPUT_TABLE = "ahg_ce_output"


class KishuDiskAHG:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(
            f"create table if not exists {AHG_VARIABLE_SNAPSHOT_TABLE} (version int, name text, deleted bool, size int)"
        )
        cur.execute(f"create table if not exists {AHG_CELL_EXECUTION_TABLE} (ce_id int, code text, runtime float)")
        cur.execute(f"create table if not exists {AHG_CE_INPUT_TABLE} (ce_id int, version int, name text)")
        cur.execute(f"create table if not exists {AHG_CE_OUTPUT_TABLE} (ce_id int, version int, name text)")
        con.commit()

    def drop_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"drop table if exists {AHG_VARIABLE_SNAPSHOT_TABLE}")
        cur.execute(f"drop table if exists {AHG_CELL_EXECUTION_TABLE}")
        cur.execute(f"drop table if exists {AHG_CE_INPUT_TABLE}")
        cur.execute(f"drop table if exists {AHG_CE_OUTPUT_TABLE}")
        con.commit()

    def store_update_results(self, update_result: AHGUpdateResult):
        # Unpack items
        accessed_vss = update_result.accessed_vss
        output_vss = update_result.output_vss
        newest_ce = update_result.newest_ce

        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        # Store each output VS.
        for vs in output_vss:
            cur.execute(
                f"insert into {AHG_VARIABLE_SNAPSHOT_TABLE} values (?, ?, ?, ?)",
                (vs.version, VersionedName.encode_name(vs.name), vs.deleted, vs.size),
            )

        # Store the newest CE.
        cur.execute(
            f"insert into {AHG_CELL_EXECUTION_TABLE} values (?, ?, ?)",
            (newest_ce.cell_num, newest_ce.cell, newest_ce.cell_runtime_s),
        )

        # Store each VS to CE edge.
        for vs in accessed_vss:
            cur.execute(
                f"insert into {AHG_CE_INPUT_TABLE} values (?, ?, ?)",
                (newest_ce.cell_num, vs.version, VersionedName.encode_name(vs.name)),
            )

        # Store each CE to VS edge.
        for vs in output_vss:
            cur.execute(
                f"insert into {AHG_CE_OUTPUT_TABLE} values (?, ?, ?)",
                (newest_ce.cell_num, vs.version, VersionedName.encode_name(vs.name)),
            )

        con.commit()

    def get_variable_snapshots(self) -> List[VariableSnapshot]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select * from {AHG_VARIABLE_SNAPSHOT_TABLE}")
        res: List = cur.fetchall()
        return [
            VariableSnapshot(VersionedName.decode_name(name), version, deleted, size) for version, name, deleted, size in res
        ]

    def get_cell_executions(self) -> List[CellExecution]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select * from {AHG_CELL_EXECUTION_TABLE}")
        res: List = cur.fetchall()
        return [CellExecution(cell_num, cell, cell_runtime_s) for cell_num, cell, cell_runtime_s in res]

    def get_vs_to_ce_edges(self) -> List[Tuple[VersionedName, int]]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select * from {AHG_CE_INPUT_TABLE}")
        res: List = cur.fetchall()
        return [(VersionedName(VersionedName.decode_name(name), version), cell_num) for cell_num, version, name in res]

    def get_ce_to_vs_edges(self) -> List[Tuple[int, VersionedName]]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"select * from {AHG_CE_OUTPUT_TABLE}")
        res: List = cur.fetchall()
        return [(cell_num, VersionedName(VersionedName.decode_name(name), version)) for cell_num, version, name in res]

    # def construct_ahg(self) -> AHG:
    #     con = sqlite3.connect(self.database_path)
    #     cur = con.cursor()

    #     # We manually set the fields of this new AHG as we are not following the regular notebook cell execution workflow.
    #     ahg = AHG()

    #     # Get all VSes
    #     cur.execute(f"select * from {AHG_VARIABLE_SNAPSHOT_TABLE}")
    #     res: List = cur.fetchall()
    #     for version, name, deleted, size in res:
    #         decoded_name = VersionedName.decode_name(name)
    #         ahg._variable_snapshots[VersionedName(decoded_name, version)] = VariableSnapshot(decoded_name, version, deleted, size)

    #     # Add cell executions.
    #     cur.execute(f"select * from {AHG_CELL_EXECUTION_TABLE} ORDER BY ce_id ASC")
    #     res: List = cur.fetchall()
    #     for cell_num, cell, cell_runtime_s in res:
    #         ahg._cell_executions[cell_num] = CellExecution(cell_num, cell, cell_runtime_s)

    #     # Add VS to CE edges.
    #     cur.execute(f"select * from {AHG_CE_INPUT_TABLE}")
    #     res: List = cur.fetchall()
    #     for cell_num, version, name in res:
    #         decoded_name = VersionedName.decode_name(name)
    #         vs = ahg._variable_snapshots[VersionedName(decoded_name, version)]
    #         ce = ahg._cell_executions[cell_num]
    #         vs.input_ces.append(ce)
    #         ce.src_vss.append(vs)

    #     # Add CE to VS edges.
    #     cur.execute(f"select * from {AHG_CE_OUTPUT_TABLE}")
    #     res: List = cur.fetchall()
    #     for cell_num, version, name in res:
    #         decoded_name = VersionedName.decode_name(name)
    #         vs = ahg._variable_snapshots[VersionedName(decoded_name, version)]
    #         ce = ahg._cell_executions[cell_num]
    #         vs.output_ce = ce
    #         ce.dst_vss.append(vs)

    #     return ahg
