"""Database operations used in the Timetracker application."""

import argparse
import pathlib
import sqlite3
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable
from typing import Literal
from typing import Sequence
from uuid import uuid4

from timetracker.server.dependencies import DB_PATH

TSqliteCol = Literal["TEXT", "NUMBER", "DATETIME", "varchar(500)"]


@dataclass
class Column:
    """Describes a column directive in a CREATE TABLE query."""

    name: str
    type_: TSqliteCol
    validators: Sequence[Callable] = field(default_factory=list)
    primary_key: bool = False
    default: str | None = None
    ref: tuple[str, str] | None = None


@dataclass
class Schema:
    """Database schema used to run queries."""

    table_name: str
    columns: Sequence[Column]

    @property
    def column_names(self) -> list[str]:
        """list[str]: Names of columns in the table."""
        return [col.name for col in self.columns]

    def _trim_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Trim a record based on existing table columns.

        Args:
            record (dict[str, Any]): Record to be trimmed.

        Returns:
            dict[str, Any]: Trimmed record.
        """
        return {k: v for k, v in record.items() if k in self.column_names}

    def _check_record(self, record: dict[str, Any]) -> None:
        """Check whether a record include invalid columns.

        Args:
            record (dict[str, Any]): Record to be checked.

        Raises:
            KeyError: If at least one column does not exist in the table.
        """
        for col in record.keys():
            if col not in self.column_names:
                msg = f"Column '{col}' in record does not exist in table!"
                raise KeyError(msg)

    def _check_columns(self, columns: Sequence[str]) -> None:
        """Check if columns exist in the table.

        Args:
            columns (Sequence[str]): Columns to check.

        Raises:
            KeyError: If at least one column does not exist in the table.
        """
        for col in columns:
            if col not in self.column_names:
                msg = f"Column '{col}' does not exist in table!"
                raise KeyError(msg)

    def _create_table_query(self, if_not_exists: bool) -> str:
        """Build a CREATE TABLE query.

        Args:
            if_not_exists (bool): Whether to include a "IF NOT EXISTS" statement.

        Returns:
            str: Resulting CREATE TABLE query.
        """
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

    def _insert_table_query(self, columns: Sequence[str]) -> str:
        """Build an INSERT query.

        Args:
            columns (Sequence[str]): Columns considered in the insert.

        Returns:
            str: Resulting INSERT query.
        """
        self._check_columns(columns)
        return (
            f"INSERT INTO {self.table_name} ("
            + ", ".join(f"{col}" for col in columns)
            + ") VALUES ("
            + ", ".join(f":{col}" for col in columns)
            + ")"
        )

    def create_table(self, con: sqlite3.Connection, if_not_exists: bool = True) -> None:
        """Create a table based on schema.

        Args:
            con (sqlite3.Connection): Database connection.
            if_not_exists (bool, optional): Only create table if it does not
            exist. Defaults to True.
        """
        con.execute(self._create_table_query(if_not_exists=if_not_exists))

    def insert_records(
        self,
        con: sqlite3.Connection,
        records: Sequence[dict[str, Any]],
        columns: Sequence[str] | None = None,
    ) -> None:
        """Insert records in the table.

        Args:
            con (sqlite3.Connection): Database connection.
            records (Sequence[dict[str, Any]]): Records to be added.
            columns (Sequence[str] | None, optional): Columns to consider in the
            insert. Defaults to None.
        """
        if columns is None:
            columns = self.column_names

        self._check_columns(columns=columns)
        con.executemany(self._insert_table_query(columns), records)
        con.commit()

    def select_all(
        self, con: sqlite3.Connection, columns: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        """Select all records in the database table.

        Args:
            con (sqlite3.Connection): Database connection.
            columns (Sequence[str] | None, optional): Columns to retrieve. Defaults
            to None.

        Returns:
            list[dict[str, Any]]: Resulting records.
        """
        return self._run_select_query(con, params=(), columns=columns)

    def update_record_by_id(
        self, con: sqlite3.Connection, id: str, new_record: dict[str, Any]
    ) -> None:
        """Update a record based on its ID.

        Args:
            con (sqlite3.Connection): Database connection.
            id (str): ID of the record to be updated.
            new_record (dict[str, Any]): Updated data.
        """
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
        """Delete database records based on id column.

        Args:
            con (sqlite3.Connection): Database connection.
            id (str): ID used for deletion.
        """
        con.execute(f"DELETE FROM {self.table_name} WHERE id = ?;", (id,))
        con.commit()

    def select_by_id(self, con: sqlite3.Connection, id: str) -> list[dict[str, Any]]:
        """Select items by the id column.

        Args:
            con (sqlite3.Connection): Database connection.
            id (str): ID used in the filter.

        Returns:
            list[dict[str, Any]]: Resulting records.
        """
        return self._run_select_query(con=con, where="WHERE id = ?;", params=(id,))

    def _run_select_query(
        self,
        con: sqlite3.Connection,
        params: tuple[Any, ...],
        columns: Sequence[str] | None = None,
        where: str | None = None,
    ) -> list[dict[str, Any]]:
        """Run a select query on the database table matching the schema.

        Args:
            con (sqlite3.Connection): Database connection.
            params (tuple[Any, ...]): Parameters for bound query elements.
            columns (Sequence[str] | None, optional): Columns to retrieve. Defaults
            to None.
            where (str | None, optional): Where statement for filtering. Defaults
            to None.

        Returns:
            list[dict[str, Any]]: Resulting records.
        """
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
    """Set up the operational database."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", action="store", default=DB_PATH)
    args = parser.parse_args()

    pathlib.Path(args.db_path).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(args.db_path) as con:
        TIME_ENTRY_SCHEMA.create_table(con, if_not_exists=True)
        WORK_ITEM_SCHEMA.create_table(con, if_not_exists=True)


if __name__ == "__main__":
    raise SystemExit(setup())
