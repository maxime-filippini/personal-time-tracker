"""Routes which relate to operations on work items."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse

from timetracker.server.db import WORK_ITEM_SCHEMA
from timetracker.server.dependencies import get_db
from timetracker.server.dependencies import templates

router = APIRouter()


@router.get("/work-items", response_class=HTMLResponse)
async def get_work_item_page(
    request: Request, db: Annotated[sqlite3.Connection, Depends(get_db)]
) -> HTMLResponse:
    """Get the web page for work items interaction.

    Args:
        request (Request): Request to be passed in context.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        HTMLResponse: HTML page for work items.
    """
    return templates.TemplateResponse(
        "pages/work-items.html",
        {"request": request, "items": WORK_ITEM_SCHEMA.select_all(db)},
    )


@router.get("/work-item", response_class=HTMLResponse)
async def get_work_item_table(
    request: Request, db: Annotated[sqlite3.Connection, Depends(get_db)]
) -> HTMLResponse:
    """Get the list of all work items, in the form of an HTML table.

    Args:
        request (Request): Request to be passed in context.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        templates.TemplateResponse: Table of all work items.
    """
    return templates.TemplateResponse(
        "fragments/work_items/table.html",
        {"request": request, "items": WORK_ITEM_SCHEMA.select_all(db)},
    )


@router.get("/work-item/form", response_class=HTMLResponse)
async def add_work_item_form(
    request: Request, id: str = "", label: str = ""
) -> HTMLResponse:
    """Get the form to add a new work item.

    Args:
        request (Request): Request to be passed in context.
        id (str, optional): ID to pre-fill the form with. Defaults to "".
        label (str, optional): Label to pre-fill the form with. Defaults to "".

    Returns:
        HTMLResponse: HTML form to add a new work item.
    """
    return templates.TemplateResponse(
        "fragments/work_items/form.html", {"request": request, "id": id, "label": label}
    )


@router.get("/work-item/{id}/edit", response_class=HTMLResponse)
async def edit_work_item_form(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    id: str,
) -> HTMLResponse:
    """Get the edit form for a work item.

    Args:
        request (Request): Request to be passed in context.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.
        id (str): ID of the work item to edit.

    Returns:
        HTMLResponse: Edit form.
    """
    items = WORK_ITEM_SCHEMA.select_by_id(db, id=id)
    item = items[0]

    return templates.TemplateResponse(
        "fragments/work_items/edit_form.html",
        {"request": request, "item": item},
    )


@router.delete("/work-item/{id}", response_class=HTMLResponse)
async def delete_work_item(
    request: Request, id: str, db: Annotated[sqlite3.Connection, Depends(get_db)]
) -> HTMLResponse:
    """Delete a work item from the database.

    Args:
        request (Request): Request to be passed in context.
        id (str): ID of the work item to be deleted.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.

    Returns:
        HTMLResponse: Updated table.
    """
    WORK_ITEM_SCHEMA.delete_record_by_id(db, id=id)
    return templates.TemplateResponse(
        "fragments/work_items/table.html",
        {"request": request, "items": WORK_ITEM_SCHEMA.select_all(db)},
    )


@router.patch("/work-item/{id}", response_class=HTMLResponse)
async def patch_work_item(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    id: str,
    label: str | None = None,
) -> HTMLResponse:
    """Patch a work item.

    Args:
        request (Request): Request to be passed in context.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.
        id (str): ID of the work item to be edited.
        label (str | None, optional): New label. Defaults to None.

    Returns:
        HTMLResponse: Updated table.
    """
    if label:
        WORK_ITEM_SCHEMA.update_record_by_id(db, id=id, new_record={"label": label})

    return templates.TemplateResponse(
        "fragments/work_items/table.html",
        {"request": request, "items": WORK_ITEM_SCHEMA.select_all(db)},
    )


@router.post("/work-item", response_class=HTMLResponse)
async def add_work_item(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    id: Annotated[str, Form()],
    label: Annotated[str, Form()],
) -> HTMLResponse:
    """Add a work item to the database.

    Args:
        request (Request): Request to be passed in context.
        db (Annotated[sqlite3.Connection, Depends): Database dependency.
        id (Annotated[str, Form): ID of the new work item.
        label (Annotated[str, Form): Label of the new work item.

    Returns:
        HTMLResponse: Updated work item table.
    """
    items = WORK_ITEM_SCHEMA.select_by_id(db, id=id)

    if items:
        # error - Do input validation here. Return form, but with the message
        return templates.TemplateResponse(
            "fragments/work_item_form.html",
            {"request": request, "id_exists": True, "id": id, "label": label},
        )

    WORK_ITEM_SCHEMA.insert_records(
        db, columns=("id", "label"), records=[{"id": id, "label": label}]
    )

    return templates.TemplateResponse(
        "fragments/work_items/table.html",
        {"request": request, "items": WORK_ITEM_SCHEMA.select_all(db)},
    )
