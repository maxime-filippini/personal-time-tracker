"""Routes related to the time tracking features."""

import sqlite3
from datetime import datetime
from datetime import timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from timetracker.server.db import TIME_ENTRY_SCHEMA
from timetracker.server.db import WORK_ITEM_SCHEMA
from timetracker.server.dependencies import get_db
from timetracker.server.dependencies import templates
from timetracker.server.utils import _convert_seconds_to_time

router = APIRouter()


@router.post("/timer/start", response_class=HTMLResponse)
async def start_timer(
    request: Request,
    selected_work_item: Annotated[str, Form()],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    task_desc: Annotated[str, Form()] = None,
) -> templates.TemplateResponse:
    """Start a timer.

    Args:
        request (Request): Request to be passed in context.
        selected_work_item (Annotated[str, Form): Current work item.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.
        task_desc (Annotated[str, Form, optional): Current task description. Defaults
        to None.

    Returns:
        templates.TemplateResponse: Either a running timer, or validation.
    """
    if not task_desc:
        return templates.TemplateResponse(
            "fragments/timer/not_running.html",
            {
                "request": request,
                "missing_description": True,
                "selected_work_item": selected_work_item,
                "work_items": [item["id"] for item in WORK_ITEM_SCHEMA.select_all(db)],
            },
        )

    return templates.TemplateResponse(
        "fragments/timer/running.html",
        {
            "request": request,
            "task_desc": task_desc,
            "selected_work_item": selected_work_item,
        },
    )


@router.post("/timer/stop", response_class=HTMLResponse)
async def stop_timer(
    request: Request,
    time_name: Annotated[str, Form()],
    work_item: Annotated[str, Form()],
    task_desc: Annotated[str, Form()],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
) -> templates.TemplateResponse:
    """Stop a running timer.

    Args:
        request (Request): Request to be passed in context.
        time_name (Annotated[str, Form): Current time.
        work_item (Annotated[str, Form): Current work item.
        task_desc (Annotated[str, Form): Current task description.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        templates.TemplateResponse: Timer in "not running" state.
    """
    TIME_ENTRY_SCHEMA.insert_records(
        db,
        columns=("id", "time", "desc", "workitem"),
        records=[
            {
                "id": str(uuid4()),
                "time": time_name,
                "desc": task_desc,
                "workitem": work_item,
            }
        ],
    )

    resp = templates.TemplateResponse(
        "fragments/timer/not_running.html",
        {
            "request": request,
            "selected_work_item": work_item,
            "work_items": [item["id"] for item in WORK_ITEM_SCHEMA.select_all(db)],
        },
    )
    resp.headers["HX-Trigger"] = "newEntry"
    return resp


@router.get("/table", response_class=HTMLResponse)
async def get_time_table(
    request: Request, offset: int, db: Annotated[sqlite3.Connection, Depends(get_db)]
) -> templates.TemplateResponse:
    """Get the list of a day's time entries.

    Args:
        request (Request): Request to be passed in context.
        offset (int): Offset in days from today.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        templates.TemplateResponse: Table of time entries.
    """
    today = datetime.today()
    date = today - timedelta(offset)
    sdate = date.strftime("%Y-%m-%d")

    entries = TIME_ENTRY_SCHEMA._run_select_query(
        db, where="WHERE DATE(timestamp) = ?", params=(sdate,)
    )

    for entry in entries:
        entry["time"] = _convert_seconds_to_time(entry["time"])

    return templates.TemplateResponse(
        "fragments/time_entry/table.html", {"request": request, "items": entries}
    )
