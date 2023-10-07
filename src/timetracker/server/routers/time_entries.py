"""Routes related to the time entries."""

import sqlite3
from pathlib import Path
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from timetracker.server.db import TIME_ENTRY_SCHEMA
from timetracker.server.dependencies import get_db
from timetracker.server.dependencies import templates
from timetracker.server.utils import _convert_seconds_to_time

router = APIRouter()

TEMPLATE_ROOT = Path("fragments/time_entry")


@router.delete("/entry/{id}", response_class=RedirectResponse)
async def delete_entry(
    request: Request, id: str, db: Annotated[sqlite3.Connection, Depends(get_db)]
) -> HTMLResponse:
    """Delete a time entry from the database.

    Args:
        request (Request): Request to be passed in context.
        id (str): ID of the time entry.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        HTMLResponse: Successful response.
    """
    TIME_ENTRY_SCHEMA.delete_record_by_id(db, id=id)
    return HTMLResponse(status_code=200)


@router.patch("/entry/{id}", response_class=RedirectResponse)
async def patch_entry(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    id: str,
    task_desc: Annotated[str, Form()],
    time: Annotated[str, Form()],
    offset: int = 0,
) -> RedirectResponse:
    """Patch a time entry.

    Args:
        request (Request): Request to be passed in context.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.
        id (str): ID of the time entry.
        task_desc (Annotated[str, Form): Description for the entry.
        time (Annotated[str, Form): Time for the entry.
        offset (int, optional): Table offset to get the correct time table
        page. Defaults to 0.

    Returns:
        RedirectResponse: Redirection to the time table.
    """
    hours, mins, seconds = time.split(":")
    time_in_seconds = int(seconds) + int(mins) * 60 + int(hours) * 60 * 60

    TIME_ENTRY_SCHEMA.update_record_by_id(
        db, id=id, new_record={"desc": task_desc, "time": time_in_seconds}
    )

    url = "/table?" + urlencode({"offset": offset})

    response = RedirectResponse(url, status_code=303)
    return response


@router.get("/entry/{id}/edit", response_class=HTMLResponse)
async def get_entry_edit_form(
    request: Request, id: str, db: Annotated[sqlite3.Connection, Depends(get_db)]
) -> HTMLResponse:
    """Get the form used to edit a time entry.

    Args:
        request (Request): Request to be passed in context.
        id (str): ID of the time entry.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        HTMLResponse: Pre-filled form for editing of time entry.
    """
    entries = TIME_ENTRY_SCHEMA._run_select_query(
        db, where="WHERE id = ?", params=(id,)
    )

    entry = entries[0]
    entry["time"] = _convert_seconds_to_time(entry["time"])

    return templates.TemplateResponse(
        str(TEMPLATE_ROOT / "edit_form.html"), {"request": request, "entry": entry}
    )
