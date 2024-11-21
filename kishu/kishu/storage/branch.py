from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from dataclasses_json import dataclass_json

from kishu.exceptions import BranchConflictError, BranchNotFoundError

BRANCH_TABLE = "branch"
HEAD_BRANCH_TABLE = "head_branch"
HEAD_KEY = "HEAD"


BRAHCN_TABLE_COMMIT_ID_IDX = "branch_commit_id_idx"


BRANCH_NAME_ADJECTIVES = [
    "agile",
    "algebraic",
    "analytic",
    "atomic",
    "biochemical",
    "biogenic",
    "catalytic",
    "chaotic",
    "chromatic",
    "complex",
    "convergent",
    "cosmic",
    "diagonal",
    "dynamic",
    "electrostatic",
    "elemental",
    "entropic",
    "exponential",
    "fractal",
    "genetic",
    "genomic",
    "geometric",
    "inertial",
    "integer",
    "intrinsic",
    "invariant",
    "ionic",
    "isotopic",
    "iterative",
    "kinematic",
    "kinetic",
    "logarithmic",
    "luminescent",
    "luminous",
    "molecular",
    "nebular",
    "nebulous",
    "neural",
    "numeric",
    "orthogonal",
    "oscillating",
    "pulsating",
    "quantum",
    "radiant",
    "radiogenic",
    "rational",
    "recursive",
    "resilient",
    "resonant",
    "scalar",
    "sonic",
    "statistical",
    "stellar",
    "subatomic",
    "symmetric",
    "thermal",
    "topological",
    "trigonometric",
    "vibrant",
    "viscous",
]


BRANCH_NAME_NOUNS = [
    "allele",
    "atom",
    "bacteria",
    "beam",
    "bolt",
    "catalyst",
    "cell",
    "core",
    "cytoplasm",
    "dna",
    "doppler",
    "electrode",
    "electron",
    "enzyme",
    "fermentation",
    "flux",
    "force",
    "fuse",
    "gene",
    "genome",
    "heat",
    "heliocentric",
    "hydrocarbon",
    "hypothesis",
    "ion",
    "isotope",
    "kinetics",
    "lens",
    "ligand",
    "light",
    "magnetism",
    "mass",
    "microorganism",
    "nebula",
    "neuron",
    "orb",
    "orbit",
    "oscillation",
    "photosynthesis",
    "pixel",
    "plasma",
    "plasmid",
    "polymer",
    "prism",
    "prokaryote",
    "proton",
    "pulse",
    "quantum",
    "quark",
    "radiance",
    "reactor",
    "rna",
    "spark",
    "spin",
    "supernova",
    "thermodynamics",
    "transcription",
    "valve",
    "vesicle",
    "wave",
]


@dataclass_json
@dataclass
class HeadBranch:
    branch_name: Optional[str]
    commit_id: Optional[str]


@dataclass
class BranchRow:
    branch_name: str
    commit_id: str


class KishuBranch:

    def __init__(self, database_path: Path):
        self.database_path = database_path

    def init_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"create table if not exists {BRANCH_TABLE} (branch_name text primary key, commit_id text)")
        cur.execute(f"create table if not exists {HEAD_BRANCH_TABLE} (head primary key, branch_name text, commit_id text)")
        cur.execute(f"create index if not exists {BRAHCN_TABLE_COMMIT_ID_IDX} on {BRANCH_TABLE} (commit_id)")
        con.commit()

    def drop_database(self):
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"drop table if exists {BRANCH_TABLE}")
        cur.execute(f"drop table if exists {HEAD_BRANCH_TABLE}")
        con.commit()

    def get_head(self) -> HeadBranch:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {HEAD_BRANCH_TABLE} where head = '{HEAD_KEY}'"
        try:
            cur.execute(query)
            res: Optional[tuple] = cur.fetchone()
            if not res:
                return HeadBranch(branch_name=None, commit_id=None)
            branch_name, commit_id = res
            return HeadBranch(branch_name=branch_name, commit_id=commit_id)
        finally:
            con.close()

    def reset_head(self) -> None:
        # Delete head to no-head state.
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        cur.execute(f"delete from {HEAD_BRANCH_TABLE} where head = '{HEAD_KEY}'")
        con.commit()

    def update_head(
        self, branch_name: Optional[str] = None, commit_id: Optional[str] = None, is_detach: bool = False
    ) -> HeadBranch:
        # Get current head.
        head = self.get_head()

        # Assign head branch.
        if is_detach:
            head.branch_name = None
        elif branch_name is not None:
            head.branch_name = branch_name

        # Assign commit ID.
        if commit_id is not None:
            head.commit_id = commit_id

        # Write head.
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"insert or replace into {HEAD_BRANCH_TABLE} values ('{HEAD_KEY}', ?, ?)"
        cur.execute(query, (head.branch_name, head.commit_id))
        con.commit()

        return head

    def upsert_branch(self, branch: str, commit_id: str) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"insert or replace into {BRANCH_TABLE} values (?, ?)"
        cur.execute(query, (branch, commit_id))
        con.commit()

    def list_branch(self) -> List[BranchRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE}"
        try:
            cur.execute(query)
            return [BranchRow(branch_name=branch_name, commit_id=commit_id) for branch_name, commit_id in cur]
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        finally:
            con.close()

    def get_branch(self, branch_name: str) -> List[BranchRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE} where branch_name = ?"
        try:
            cur.execute(query, (branch_name,))
            return [BranchRow(branch_name=branch_name, commit_id=commit_id) for branch_name, commit_id in cur]
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        finally:
            con.close()

    def branches_for_commit(self, commit_id: str) -> List[BranchRow]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = f"select branch_name, commit_id from {BRANCH_TABLE} where commit_id = ?"
        try:
            cur.execute(query, (commit_id,))
            return [BranchRow(branch_name=branch_name, commit_id=commit_id) for branch_name, commit_id in cur]
        except sqlite3.OperationalError:
            # No such table means no branch
            return []
        finally:
            con.close()

    def branches_for_many_commits(
        self,
        commit_ids: List[str],
    ) -> Dict[str, List[BranchRow]]:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()
        query = "select branch_name, commit_id from {} where commit_id in ({})".format(
            BRANCH_TABLE, ", ".join("?" * len(commit_ids))
        )
        try:
            cur.execute(query, commit_ids)
        except sqlite3.OperationalError:
            # No such table means no branch
            return {}
        raw_branches = cur.fetchall()
        branch_by_commit: Dict[str, List[BranchRow]] = {}
        for branch_name, commit_id in raw_branches:
            if commit_id not in branch_by_commit:
                branch_by_commit[commit_id] = []
            branch_by_commit[commit_id].append(
                BranchRow(
                    branch_name=branch_name,
                    commit_id=commit_id,
                )
            )
        con.close()
        return branch_by_commit

    def delete_branch(self, branch_name: str) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        head = self.get_head()
        if branch_name == head.branch_name:
            raise BranchConflictError("Cannot delete the currently checked-out branch.")
        if not KishuBranch._contains_branch(cur, branch_name):
            raise BranchNotFoundError(branch_name)

        query = f"delete from {BRANCH_TABLE} where branch_name = ?"
        cur.execute(query, (branch_name,))
        con.commit()

    def rename_branch(self, old_name: str, new_name: str) -> None:
        con = sqlite3.connect(self.database_path)
        cur = con.cursor()

        if not KishuBranch._contains_branch(cur, old_name):
            raise BranchNotFoundError(old_name)
        if KishuBranch._contains_branch(cur, new_name):
            raise BranchConflictError("The provided new branch name already exists.")

        query = f"update {BRANCH_TABLE} set branch_name = ? where branch_name = ?"
        cur.execute(query, (new_name, old_name))
        con.commit()

        # Update HEAD branch if HEAD is on branch
        head = self.get_head()
        if old_name == head.branch_name:
            self.update_head(branch_name=new_name)

    @staticmethod
    def random_branch_name() -> str:
        adj_idx = random.randint(0, len(BRANCH_NAME_ADJECTIVES) - 1)
        noun_idx = random.randint(0, len(BRANCH_NAME_NOUNS) - 1)
        return f"{BRANCH_NAME_ADJECTIVES[adj_idx]}_{BRANCH_NAME_NOUNS[noun_idx]}"

    @staticmethod
    def _contains_branch(cur: sqlite3.Cursor, branch_name: str) -> bool:
        query = f"select count(*) from {BRANCH_TABLE} where branch_name = ?"
        cur.execute(query, (branch_name,))
        return cur.fetchone()[0] == 1
