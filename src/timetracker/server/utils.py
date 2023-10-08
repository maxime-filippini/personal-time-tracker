"""Utilities for the application."""


import sqlite3
from datetime import datetime
from datetime import timedelta
from typing import Any

from timetracker.server.db import TIME_ENTRY_SCHEMA


def _convert_seconds_to_time(seconds: int) -> str:
    """Convert a number of seconds to a HH:MM:SS time.

    Args:
        seconds (int): Time in seconds.

    Returns:
        str: Formatted time.
    """
    mins, rem_s = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02}:{mins:02}:{rem_s:02}"


def get_daily_time_entries(
    con: sqlite3.Connection, offset: int = 0
) -> list[dict[str, Any]]:
    """Get the time entries for a given day.

    Args:
        con (sqlite3.Connection): Database connection.
        offset (int, optional): How many days before today. Defaults to 0.

    Returns:
        list[dict[str, Any]]: Resulting records.
    """
    today = datetime.today()
    date = today - timedelta(offset)
    sdate = date.strftime("%Y-%m-%d")

    entries = TIME_ENTRY_SCHEMA._run_select_query(
        con, where="WHERE DATE(timestamp) = ?", params=(sdate,)
    )

    for entry in entries:
        entry["time"] = _convert_seconds_to_time(entry["time"])

    return entries
