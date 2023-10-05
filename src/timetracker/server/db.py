import argparse
from dataclasses import dataclass, field
import sqlite3
from typing import Any, Callable, Literal, Optional, Sequence
from uuid import uuid4
import pathlib

DB_PATH = pathlib.Path.home() / ".timetracker" / "db.db"

TSqliteCol = Literal["TEXT", "NUMBER", "DATETIME", "varchar(500)"]


@dataclass
class Column:
    name: str
    type_: TSqliteCol
    validators: Sequence[Callable] = field(default_factory=list)
    primary_key: bool = False
    default: str | None = None
    ref: tuple[str, str] | None = None


@dataclass
class Schema:
    table_name: str
    columns: Sequence[Column]

    @property
    def column_names(self):
        return [col.name for col in self.columns]

    def _trim_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in record.items() if k in self.column_names}

    def _check_record(self, record: dict[str, Any]) -> None:
        for col in record.keys():
            if col not in self.column_names:
                raise KeyError(f"Column '{col}' in record does not exist in table!")

    def _check_columns(self, columns: Sequence[str]) -> None:
        for col in columns:
            if col not in self.column_names:
                raise KeyError(f"Column '{col}' does not exist in table!")

    def _create_table_query(self, if_not_exists: bool) -> str:
        query_columns = []

        for column in self.columns:
            if column.ref:
                ref_table, ref_col = column.ref
                new_col = (
                    f"FOREIGN KEY({column.name}) REFERENCES {ref_table}({ref_col})"
                )

            else:
                new_col = f"{column.name} {column.type_}"

                if column.primary_key:
                    new_col += " PRIMARY KEY"

                if column.default:
                    new_col += f" DEFAULT {column.default}"

            query_columns.append(new_col)

        column_section = ", ".join(query_columns)

        query_elements = ["CREATE TABLE"]
        if if_not_exists:
            query_elements.append("IF NOT EXISTS")

        query_elements.append(f"{self.table_name}({column_section});")

        return " ".join(query_elements)

    def _insert_table_query(self, columns: Sequence[str]) -> None:
        self._check_columns(columns)
        return (
            f"INSERT INTO {self.table_name} ("
            + ", ".join(f"{col}" for col in columns)
            + ") VALUES ("
            + ", ".join(f":{col}" for col in columns)
            + ")"
        )

    def create_table(self, con: sqlite3.Connection, if_not_exists: bool = True) -> None:
        con.execute(self._create_table_query(if_not_exists=if_not_exists))

    def insert_records(
        self,
        con: sqlite3.Connection,
        records: Sequence[dict[str, Any]],
        columns: Sequence[str] | None = None,
    ) -> None:
        if columns is None:
            columns = self.column_names

        self._check_columns(columns=columns)
        con.executemany(self._insert_table_query(columns), records)
        con.commit()

    def select_all(self, con: sqlite3.Connection, columns: Sequence[str] | None = None):
        return self._run_select_query(con, params=(), columns=columns)

    def update_record_by_id(
        self, con: sqlite3.Connection, id: str, new_record: dict[str, Any]
    ) -> None:
        self._check_record(new_record)

        query = (
            f"UPDATE {self.table_name} "
            + "SET "
            + ", ".join(
                f"{col} = :{col}"
                for col, value in new_record.items()
                if value is not None
            )
            + " WHERE id = :id"
        )

        con.execute(query, new_record | {"id": id})
        con.commit()

    def delete_record_by_id(self, con: sqlite3.Connection, id: str) -> None:
        con.execute(f"DELETE FROM {self.table_name} WHERE id = ?;", (id,))

    def _run_select_query(
        self,
        con: sqlite3.Connection,
        params: tuple[Any, ...],
        columns: Sequence[str] | None = None,
        where: str | None = None,
    ) -> list[dict[str, Any]]:
        if columns is None:
            columns = self.column_names
        else:
            self._check_columns(columns)

        col_str = ", ".join(columns)

        query = f"SELECT {col_str} FROM {self.table_name} " + (
            where if where is not None else ""
        )

        cur = con.execute(query, params)
        records = cur.fetchall()

        return [dict(zip(columns, record)) for record in records]


TIME_ENTRY_SCHEMA = Schema(
    table_name="entries",
    columns=(
        Column(name="id", type_="varchar(500)", primary_key=True),
        Column(name="time", type_="NUMBER"),
        Column(name="workitem", type_="TEXT"),
        Column(name="desc", type_="TEXT"),
        Column(name="timestamp", type_="DATETIME", default="CURRENT_TIMESTAMP"),
    ),
)

WORK_ITEM_SCHEMA = Schema(
    table_name="workitems",
    columns=(
        Column(name="id", type_="varchar(500)", primary_key=True),
        Column(name="label", type_="TEXT"),
        Column(name="timestamp", type_="DATETIME", default="CURRENT_TIMESTAMP"),
    ),
)


TIME_ENTRIES_SEED = (
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

WORK_ITEMS_SEED = (
    {"id": "AAA-BBB", "label": "Some client"},
    {"id": "AAA-CCC", "label": "Internal project"},
    {"id": "DDD-BBB", "label": "Training"},
    {"id": "CCC-AAA", "label": "Eh"},
    {"id": "AAA-ZZZ", "label": "Testing"},
)


def setup() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", action="store", default=DB_PATH)

    args = parser.parse_args()

    pathlib.Path(args.db_path).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(args.db_path) as con:
        TIME_ENTRY_SCHEMA.create_table(con, if_not_exists=True)
        TIME_ENTRY_SCHEMA.insert_records(con, records=TIME_ENTRIES_SEED)

        WORK_ITEM_SCHEMA.create_table(con, if_not_exists=True)
        WORK_ITEM_SCHEMA.insert_records(
            con, records=WORK_ITEMS_SEED, columns=("id", "label")
        )


if __name__ == "__main__":
    raise SystemExit(setup())
