from datetime import datetime, timedelta
import pathlib
import sqlite3
from typing import Annotated
from urllib.parse import urlencode
from uuid import uuid4
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from .db import fetch_entries, fetch_work_items, get_entry_by_id

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

DB_PATH = pathlib.Path.home() / ".timetracker" / "db.db"
SQL_ADD_ENTRY = """INSERT INTO entries (id, time, workitem, desc) VALUES(:id, :time, :workitem, :desc)"""


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
):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            SQL_ADD_ENTRY,
            {
                "id": str(uuid4()),
                "time": time_name,
                "desc": task_desc,
                "workitem": work_item,
            },
        )

    resp = templates.TemplateResponse(
        "fragments/timer/not_running.html", {"request": request}
    )
    resp.headers["HX-Trigger"] = "newEntry"
    return resp


def make_time(seconds: int) -> str:
    rem_s = seconds % 60
    hours, mins = divmod(seconds - rem_s, 60)
    return f"{hours:02}:{mins:02}:{rem_s:02}"


@app.get("/table", response_class=HTMLResponse)
async def get_time_table(request: Request, offset: int):
    today = datetime.today()
    date = today - timedelta(offset)
    sdate = date.strftime("%Y-%m-%d")

    entries = fetch_entries(date=sdate)
    for entry in entries:
        entry["time"] = make_time(entry["time"])

    return templates.TemplateResponse(
        "fragments/time_table.html", {"request": request, "items": entries}
    )


@app.get("/track", response_class=HTMLResponse)
async def get_timer_page(request: Request):
    return templates.TemplateResponse("pages/track.html", {"request": request})


@app.get("/work-items", response_class=HTMLResponse)
async def get_work_item_page(request: Request):
    return templates.TemplateResponse(
        "pages/work-items.html", {"request": request, "items": fetch_work_items()}
    )


@app.get("/analytics", response_class=HTMLResponse)
async def get_work_item_page(request: Request):
    return templates.TemplateResponse("pages/analytics.html", {"request": request})


@app.get("/all-work-items", response_class=HTMLResponse)
async def get_all_work_items(request: Request):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        res = cur.execute("SELECT * FROM workitems")
        out = res.fetchall()

    items = [item[0] for item in out]

    return templates.TemplateResponse(
        "work_item_options.html", {"request": request, "items": items}
    )


@app.get("/entry/{id}/edit", response_class=HTMLResponse)
async def get_entry_edit_form(request: Request, id: str):
    entry = get_entry_by_id(id)

    entry["time"] = make_time(entry["time"])

    return templates.TemplateResponse(
        "fragments/time_entry_form.html", {"request": request, "entry": entry}
    )


class TimeEntry(BaseModel):
    workitem: str
    desc: str
    time: str


@app.patch("/entry/{id}", response_class=RedirectResponse)
async def patch_entry(request: Request, id: str, offset: int = 0):
    print(id)

    url = "/table?" + urlencode({"offset": offset})

    response = RedirectResponse(url, status_code=303)
    return response
