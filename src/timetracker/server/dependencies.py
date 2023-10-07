"""Dependencies to be injected in the application routes."""

import pathlib
import sqlite3
from typing import Generator

from fastapi.templating import Jinja2Templates

DB_PATH = pathlib.Path.home() / ".timetracker" / "db.db"

templates = Jinja2Templates(directory="templates")


async def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Database dependency.

    Yields:
        Generator[sqlite3.Connection, None, None]: Database connection.
    """
    yield sqlite3.connect(DB_PATH, check_same_thread=False)
