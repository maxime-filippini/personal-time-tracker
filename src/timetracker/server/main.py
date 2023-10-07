"""Time tracker application, using FastAPI.

This module defines the application's server and its components.

"""

import sqlite3
from typing import Annotated

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from timetracker.server.db import WORK_ITEM_SCHEMA
from timetracker.server.dependencies import get_db
from timetracker.server.routers import time_entries
from timetracker.server.routers import timesheet
from timetracker.server.routers import tracking
from timetracker.server.routers import work_items

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/public", StaticFiles(directory="public"), name="public")

app.include_router(time_entries.router)
app.include_router(tracking.router)
app.include_router(work_items.router)
app.include_router(timesheet.router)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=RedirectResponse)
async def get_index_page(request: Request) -> RedirectResponse:
    """Index page for the front end of the application.

    Args:
        request (Request): Request to be passed in context.

    Returns:
        RedirectResponse: Redirection to the "track" page.
    """
    return RedirectResponse("/track")


@app.get("/track", response_class=HTMLResponse)
async def get_timer_page(
    request: Request, db: Annotated[sqlite3.Connection, Depends(get_db)]
) -> HTMLResponse:
    """Timer page for the front end of the application.

    Args:
        request (Request): Request to be passed in context.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        HTMLResponse: Page to be served.
    """
    return templates.TemplateResponse(
        "pages/track.html",
        {
            "request": request,
            "work_items": [item["id"] for item in WORK_ITEM_SCHEMA.select_all(db)],
        },
    )


@app.get("/timesheet", response_class=HTMLResponse)
async def get_timesheet_page(request: Request) -> HTMLResponse:
    """Timesheet page for the front end of the application.

    Args:
        request (Request): Request to be passed in context.

    Returns:
        HTMLResponse: Page to be served.
    """
    return templates.TemplateResponse("pages/timesheet.html", {"request": request})
