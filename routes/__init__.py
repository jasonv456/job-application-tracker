"""Shared helpers for the route blueprints."""
from datetime import date, datetime

from flask import abort, flash

from db import query_one

# MySQL error numbers we translate into friendly messages
ER_ROW_IS_REFERENCED = 1451   # delete blocked by a child row (FK)
ER_NO_REFERENCED_ROW = 1452   # insert/update points at a missing parent (FK)


def get_or_404(sql, params):
    row = query_one(sql, params)
    if row is None:
        abort(404)
    return row


def row_to_form(row):
    """Convert a DB row into string values suitable for pre-filling a form."""
    form = {}
    for key, value in row.items():
        if value is None:
            form[key] = ""
        elif isinstance(value, datetime):
            form[key] = value.strftime("%Y-%m-%dT%H:%M")
        elif isinstance(value, date):
            form[key] = value.isoformat()
        else:
            form[key] = value
    return form


def flash_db_error(err, action):
    if getattr(err, "errno", None) == ER_NO_REFERENCED_ROW:
        flash(f"Could not {action}: the selected related record no longer exists.", "error")
    else:
        flash(f"Could not {action}: database error ({getattr(err, 'msg', err)}).", "error")
