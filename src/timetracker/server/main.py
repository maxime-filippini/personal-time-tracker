from datetime import datetime, timedelta
import pathlib
import sqlite3
from typing import Annotated
from urllib.parse import urlencode
from uuid import uuid4
from fastapi import Depends, FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from timetracker.server.db import (
    TIME_ENTRY_SCHEMA,
    WORK_ITEM_SCHEMA,
)
from timetracker.server.db import TIME_ENTRY_SCHEMA

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

DB_PATH = pathlib.Path.home() / ".timetracker" / "db.db"


async def get_db():
    yield sqlite3.connect(DB_PATH)


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("/pages/index.html", {"request": request})


@app.post("/timer/start", response_class=HTMLResponse)
async def start_timer(
    request: Request,
    work_item: Annotated[str, Form()],
    task_desc: Annotated[str, Form()] = None,
):
    if not task_desc:
        return templates.TemplateResponse(
            "fragments/timer/not_running.html",
            {"request": request, "missing_description": True, "work_item": work_item},
        )

    return templates.TemplateResponse(
        "fragments/timer/running.html",
        {"request": request, "task_desc": task_desc, "work_item": work_item},
    )


@app.post("/timer/stop", response_class=HTMLResponse)
async def stop_timer(
    request: Request,
    time_name: Annotated[str, Form()],
    work_item: Annotated[str, Form()],
    task_desc: Annotated[str, Form()],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
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
        "fragments/timer/not_running.html", {"request": request}
    )
    resp.headers["HX-Trigger"] = "newEntry"
    return resp


def _make_time(seconds: int) -> str:
    mins, rem_s = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02}:{mins:02}:{rem_s:02}"


@app.get("/table", response_class=HTMLResponse)
async def get_time_table(
    request: Request, offset: int, db: Annotated[sqlite3.Connection, Depends(get_db)]
):
    today = datetime.today()
    date = today - timedelta(offset)
    sdate = date.strftime("%Y-%m-%d")

    entries = TIME_ENTRY_SCHEMA._run_select_query(
        db, where="WHERE DATE(timestamp) = ?", params=(sdate,)
    )

    for entry in entries:
        entry["time"] = _make_time(entry["time"])

    return templates.TemplateResponse(
        "fragments/time_table.html", {"request": request, "items": entries}
    )


@app.get("/track", response_class=HTMLResponse)
async def get_timer_page(request: Request):
    return templates.TemplateResponse("pages/track.html", {"request": request})


@app.get("/work-items", response_class=HTMLResponse)
async def get_work_item_page(
    request: Request, db: Annotated[sqlite3.Connection, Depends(get_db)]
):
    work_items = WORK_ITEM_SCHEMA.select_all(db)
    return templates.TemplateResponse(
        "pages/work-items.html", {"request": request, "items": work_items}
    )


@app.get("/analytics", response_class=HTMLResponse)
async def get_work_item_page(request: Request):
    return templates.TemplateResponse("pages/analytics.html", {"request": request})


@app.get("/all-work-items", response_class=HTMLResponse)
async def get_all_work_items(
    request: Request, db: Annotated[sqlite3.Connection, Depends(get_db)]
):
    out = WORK_ITEM_SCHEMA.select_all(db)
    items = [item["id"] for item in out]

    return templates.TemplateResponse(
        "fragments/work_item_options.html", {"request": request, "items": items}
    )


@app.get("/entry/{id}/edit", response_class=HTMLResponse)
async def get_entry_edit_form(
    request: Request, id: str, db: Annotated[sqlite3.Connection, Depends(get_db)]
):
    entries = TIME_ENTRY_SCHEMA._run_select_query(
        db, where="WHERE id = ?", params=(id,)
    )

    entry = entries[0]
    entry["time"] = _make_time(entry["time"])

    return templates.TemplateResponse(
        "fragments/time_entry_form.html", {"request": request, "entry": entry}
    )


@app.delete("/entry/{id}", response_class=RedirectResponse)
async def delete_entry(
    request: Request, id: str, db: Annotated[sqlite3.Connection, Depends(get_db)]
):
    TIME_ENTRY_SCHEMA.delete_record_by_id(db, id=id)
    return HTMLResponse(status_code=200)


@app.patch("/entry/{id}", response_class=RedirectResponse)
async def patch_entry(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    id: str,
    task_desc: Annotated[str, Form()],
    time: Annotated[str, Form()],
    offset: int = 0,
):
    hours, mins, seconds = time.split(":")
    time_in_seconds = int(seconds) + int(mins) * 60 + int(hours) * 60 * 60

    TIME_ENTRY_SCHEMA.update_record_by_id(
        db, id=id, new_record={"desc": task_desc, "time": time_in_seconds}
    )

    url = "/table?" + urlencode({"offset": offset})

    response = RedirectResponse(url, status_code=303)
    return response
