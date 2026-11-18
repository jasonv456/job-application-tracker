"""CRUD routes for the applications table."""
from datetime import date

import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute, query_all, query_one
from routes import flash_db_error, get_or_404, row_to_form
from validation import APPLICATION_STATUSES, validate_application

bp = Blueprint("applications", __name__, url_prefix="/applications")

FIELDS = ["job_id", "application_date", "status", "resume_version", "cover_letter_sent",
          "response_date", "interview_date", "notes"]

APP_SELECT = """SELECT a.*, j.job_title, c.company_id, c.company_name
                FROM applications a
                JOIN jobs j ON j.job_id = a.job_id
                JOIN companies c ON c.company_id = j.company_id"""


def _jobs():
    return query_all(
        """SELECT j.job_id, j.job_title, c.company_name FROM jobs j
           JOIN companies c ON c.company_id = j.company_id
           ORDER BY c.company_name, j.job_title"""
    )


def _check_job(data, errors):
    if "job_id" not in errors and data.get("job_id") is not None:
        if not query_one("SELECT 1 AS ok FROM jobs WHERE job_id = %s", (data["job_id"],)):
            errors["job_id"] = "Please choose an existing job."


def _render_form(form, errors, application, status=200):
    return render_template("applications/form.html", form=form, errors=errors,
                           application=application, jobs=_jobs(),
                           statuses=APPLICATION_STATUSES), status


@bp.route("/")
def list_applications():
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    where, params = [], []
    if status:
        where.append("a.status = %s")
        params.append(status)
    if q:
        where.append("(j.job_title LIKE %s OR c.company_name LIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    sql = APP_SELECT + (" WHERE " + " AND ".join(where) if where else "") + \
        " ORDER BY a.application_date DESC, a.application_id DESC"
    return render_template("applications/list.html", applications=query_all(sql, tuple(params)),
                           statuses=APPLICATION_STATUSES, status=status, q=q)


@bp.route("/<int:application_id>")
def detail(application_id):
    application = get_or_404(APP_SELECT + " WHERE a.application_id = %s", (application_id,))
    return render_template("applications/detail.html", application=application)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        data, errors = validate_application(request.form)
        _check_job(data, errors)
        if not errors:
            try:
                new_id, _ = execute(
                    f"INSERT INTO applications ({', '.join(FIELDS)}) VALUES ({', '.join(['%s'] * len(FIELDS))})",
                    tuple(data[f] for f in FIELDS),
                )
                flash("Application created.", "success")
                return redirect(url_for("applications.detail", application_id=new_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "create application")
        return _render_form(request.form, errors, None, 400)
    form = {"job_id": request.args.get("job_id", ""), "application_date": date.today().isoformat(),
            "status": "Applied"}
    return _render_form(form, {}, None)


@bp.route("/<int:application_id>/edit", methods=["GET", "POST"])
def edit(application_id):
    application = get_or_404(APP_SELECT + " WHERE a.application_id = %s", (application_id,))
    if request.method == "POST":
        data, errors = validate_application(request.form)
        _check_job(data, errors)
        if not errors:
            try:
                execute(
                    f"UPDATE applications SET {', '.join(f + ' = %s' for f in FIELDS)} WHERE application_id = %s",
                    tuple(data[f] for f in FIELDS) + (application_id,),
                )
                flash("Application updated.", "success")
                return redirect(url_for("applications.detail", application_id=application_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "update application")
        return _render_form(request.form, errors, application, 400)
    return _render_form(row_to_form(application), {}, application)


@bp.route("/<int:application_id>/delete", methods=["POST"])
def delete(application_id):
    get_or_404("SELECT application_id FROM applications WHERE application_id = %s", (application_id,))
    try:
        execute("DELETE FROM applications WHERE application_id = %s", (application_id,))
        flash("Application deleted.", "success")
    except mysql.connector.Error as err:
        flash_db_error(err, "delete application")
        return redirect(url_for("applications.detail", application_id=application_id))
    return redirect(url_for("applications.list_applications"))
