"""
Sqlite interface for storing checkpoints.
"""
import sqlite3


CHECKPOINT_TABLE = 'checkpoint'


class KishuCheckpoint:
    def __init__(self, dbfile: str):
        self.dbfile = dbfile

    def _save_into_table(self, table_name: str, commit_id: str, data: bytes) -> None:
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            "insert into {} values (?, ?)".format(table_name),
            (commit_id, memoryview(data))
        )
        con.commit()

    def init_database(self):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(f'create table if not exists {CHECKPOINT_TABLE} (commit_id text primary key, data blob)')
        con.commit()

    def get_checkpoint(self, commit_id: str) -> bytes:
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            f"select data from {CHECKPOINT_TABLE} where commit_id = ?",
            (commit_id, )
        )
        res: tuple = cur.fetchone()
        result = res[0]
        con.commit()
        return result

    def store_checkpoint(self, commit_id: str, data: bytes) -> None:
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute(
            f"insert into {CHECKPOINT_TABLE} values (?, ?)",
            (commit_id, memoryview(data))
        )
        con.commit()
