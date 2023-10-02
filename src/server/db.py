import sqlite3
from uuid import uuid4
import pathlib

DB_PATH = pathlib.Path.home() / ".timetracker" / "db.db"

SQL_ENTRY_TABLE = """CREATE TABLE IF NOT EXISTS entries(
    id varchar(500) PRIMARY KEY,
    time NUMBER,
    workitem TEXT,
    desc TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(workitem) REFERENCES workitems(id)
)"""

SQL_ENTRY_COLS = ("id", "time", "workitem", "desc", "timestamp")

SQL_ADD_ENTRY = """INSERT INTO entries (id, time, workitem, desc) 
    VALUES(:id, :time, :workitem, :desc)
"""

SQL_ADD_ENTRY_FULL = """INSERT INTO entries (id, time, workitem, desc, timestamp) 
    VALUES(:id, :time, :workitem, :desc, :timestamp)
"""

SQL_WORK_ITEMS_TABLE = """CREATE TABLE IF NOT EXISTS workitems(
    id TEXT PRIMARY KEY,
    label TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)"""

SQL_WORK_ITEMS_COLS = ("id", "label", "timestamp")

SQL_ADD_WORK_ITEM = """INSERT INTO workitems (id, label) VALUES(:id, :label)"""

ENTRY_TEST = (
    {
        "id": str(uuid4()),
        "time": 60,
        "desc": "something quick",
        "workitem": "AAA-CCC",
        "timestamp": "2023-09-28 00:00:00",
    },
    {
        "id": str(uuid4()),
        "time": 600,
        "desc": "something longer",
        "workitem": "AAA-BBB",
        "timestamp": "2023-09-28 00:00:00",
    },
    {
        "id": str(uuid4()),
        "time": 6000,
        "desc": "something longerer",
        "workitem": "DDD-BBB",
        "timestamp": "2023-06-30 00:00:00",
    },
    {
        "id": str(uuid4()),
        "time": 60000,
        "desc": "something longeeeeeer",
        "workitem": "AAA-ZZZ",
        "timestamp": "2023-06-30 00:00:00",
    },
)

WORK_ITEMS_TEST = (
    {"id": "AAA-BBB", "label": "Some client"},
    {"id": "AAA-CCC", "label": "Internal project"},
    {"id": "DDD-BBB", "label": "Training"},
    {"id": "CCC-AAA", "label": "Eh"},
    {"id": "AAA-ZZZ", "label": "Testing"},
)


def get_entry_by_id(id: str):
    with sqlite3.connect(DB_PATH) as con:
        res = con.execute("SELECT * FROM entries WHERE id = ?", (id,))
        records = res.fetchall()

    out = {k: v for k, v in zip(SQL_ENTRY_COLS, records[0])}

    return out


def fetch_entries(date: str):
    query = "SELECT * FROM entries WHERE DATE(timestamp) = ?;"

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        res = cur.execute(query, (date,))
        records = res.fetchall()

    out = [{k: v for k, v in zip(SQL_ENTRY_COLS, record)} for record in records]

    return out


def fetch_work_items():
    query = "SELECT * FROM workitems"

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        res = cur.execute(query)
        records = res.fetchall()

    out = [{k: v for k, v in zip(SQL_WORK_ITEMS_COLS, record)} for record in records]

    return out


def setup_database(path: str) -> None:
    with sqlite3.connect(path) as con:
        cur = con.cursor()

        cur.execute(SQL_WORK_ITEMS_TABLE)
        cur.execute(SQL_ENTRY_TABLE)

        cur.executemany(SQL_ADD_WORK_ITEM, WORK_ITEMS_TEST)
        cur.executemany(SQL_ADD_ENTRY_FULL, ENTRY_TEST)


if __name__ == "__main__":
    home_path = pathlib.Path.home() / ".timetracker"
    home_path.mkdir(parents=True, exist_ok=True)
    raise SystemExit(setup_database(path=home_path / "db.db"))
