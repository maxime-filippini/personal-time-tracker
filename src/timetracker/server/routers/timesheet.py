"""Routes that relate to the building of timesheets."""

import sqlite3
from collections import defaultdict
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from timetracker.server.db import TIME_ENTRY_SCHEMA
from timetracker.server.dependencies import get_db
from timetracker.server.dependencies import templates

router = APIRouter()


@router.get("/timesheet/table", response_class=HTMLResponse)
def get_timesheet(
    request: Request,
    start_date: Annotated[str, Form],
    end_date: Annotated[str, Form],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
) -> HTMLResponse:
    """Build a timesheet based on time entries.

    Args:
        request (Request): Request to be passed in context.
        start_date (Annotated[str, Form]): Start date for the timesheet.
        end_date (Annotated[str, Form]): End date for the timesheet.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        HTMLResponse: Timesheet table.
    """
    all_times = TIME_ENTRY_SCHEMA._run_select_query(
        db,
        where="WHERE timestamp BETWEEN DATE(?) AND DATE(?)",
        params=(start_date, end_date),
    )

    # A timesheet has two axes - Workitems and dates
    u_workitems = set(time["workitem"] for time in all_times)
    u_dates = set(
        datetime.strptime(time["timestamp"], "%Y-%m-%d %H:%M:%S")
        .date()
        .strftime("%d/%m")
        for time in all_times
    )

    timesheet_data = defaultdict(lambda: defaultdict(list))

    for time in all_times:
        date = datetime.strptime(time["timestamp"], "%Y-%m-%d %H:%M:%S")
        timesheet_data[time["workitem"]][date.date().strftime("%d/%m")].append(
            {key: time[key] for key in ("time", "desc")}
        )

    # Aggregation
    out = []

    for workitem in u_workitems:
        row = []

        for date in u_dates:
            daily_items = timesheet_data[workitem][date]
            total_time_in_hours = round(
                sum(item["time"] for item in daily_items) / 3600, 2
            )
            comment = " / ".join(set(item["desc"] for item in daily_items))

            if not comment:
                comment = "No comment"

            row.append({"time": total_time_in_hours, "comment": comment})

        out.append(row)

    return templates.TemplateResponse(
        "fragments/timesheet/table.html",
        {
            "request": request,
            "col_labels": list(u_dates),
            "rows": zip(u_workitems, out),
        },
    )
