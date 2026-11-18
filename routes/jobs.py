"""CRUD routes for the jobs table (including the JSON `requirements` column)."""
import json

import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import execute, query_all, query_one
from matching import calculate_match, match_level, parse_skills
from routes import flash_db_error, get_or_404, row_to_form
from validation import JOB_TYPES, validate_job

bp = Blueprint("jobs", __name__, url_prefix="/jobs")

FIELDS = ["company_id", "job_title", "job_description", "requirements", "salary_min",
          "salary_max", "job_type", "posting_url", "date_posted", "is_active"]

JOB_SELECT = """SELECT j.*, c.company_name
                FROM jobs j JOIN companies c ON c.company_id = j.company_id"""


def _companies():
    return query_all("SELECT company_id, company_name FROM companies ORDER BY company_name")


def _with_skills(job):
    job["skills"] = parse_skills(job.get("requirements"))
    return job


def _params(data):
    values = dict(data)
    values["requirements"] = json.dumps(data["requirements"])
    return tuple(values[f] for f in FIELDS)


def _check_company(data, errors):
    if "company_id" not in errors and data.get("company_id") is not None:
        if not query_one("SELECT 1 AS ok FROM companies WHERE company_id = %s", (data["company_id"],)):
            errors["company_id"] = "Please choose an existing company."


def _render_form(form, errors, job, status=200):
    return render_template("jobs/form.html", form=form, errors=errors, job=job,
                           companies=_companies(), job_types=JOB_TYPES), status


@bp.route("/")
def list_jobs():
    q = request.args.get("q", "").strip()
    sql, params = JOB_SELECT, ()
    if q:
        # Search title, company, or any skill inside the JSON requirements array
        sql += """ WHERE j.job_title LIKE %s OR c.company_name LIKE %s
                   OR JSON_SEARCH(LOWER(j.requirements), 'one', %s) IS NOT NULL"""
        params = (f"%{q}%", f"%{q}%", f"%{q.lower()}%")
    sql += " ORDER BY j.is_active DESC, j.job_title"
    jobs = [_with_skills(j) for j in query_all(sql, params)]
    return render_template("jobs/list.html", jobs=jobs, q=q)


@bp.route("/<int:job_id>")
def detail(job_id):
    job = _with_skills(get_or_404(JOB_SELECT + " WHERE j.job_id = %s", (job_id,)))
    applications = query_all(
        "SELECT * FROM applications WHERE job_id = %s ORDER BY application_date DESC", (job_id,)
    )
    my_skills = session.get("skills", [])
    match = calculate_match(my_skills, job["skills"]) if my_skills else None
    level = match_level(match["percent"]) if match else None
    return render_template("jobs/detail.html", job=job, applications=applications,
                           match=match, level=level, my_skills=my_skills)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        data, errors = validate_job(request.form)
        _check_company(data, errors)
        if not errors:
            try:
                new_id, _ = execute(
                    f"INSERT INTO jobs ({', '.join(FIELDS)}) VALUES ({', '.join(['%s'] * len(FIELDS))})",
                    _params(data),
                )
                flash(f"Job “{data['job_title']}” created.", "success")
                return redirect(url_for("jobs.detail", job_id=new_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "create job")
        return _render_form(request.form, errors, None, 400)
    form = {"company_id": request.args.get("company_id", ""), "is_active": 1}
    return _render_form(form, {}, None)


@bp.route("/<int:job_id>/edit", methods=["GET", "POST"])
def edit(job_id):
    job = get_or_404(JOB_SELECT + " WHERE j.job_id = %s", (job_id,))
    if request.method == "POST":
        data, errors = validate_job(request.form)
        _check_company(data, errors)
        if not errors:
            try:
                execute(
                    f"UPDATE jobs SET {', '.join(f + ' = %s' for f in FIELDS)} WHERE job_id = %s",
                    _params(data) + (job_id,),
                )
                flash("Job updated.", "success")
                return redirect(url_for("jobs.detail", job_id=job_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "update job")
        return _render_form(request.form, errors, job, 400)
    form = row_to_form(job)
    form["requirements"] = ", ".join(parse_skills(job.get("requirements")))
    return _render_form(form, {}, job)


@bp.route("/<int:job_id>/delete", methods=["POST"])
def delete(job_id):
    job = get_or_404("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    n = query_one("SELECT COUNT(*) AS n FROM applications WHERE job_id = %s", (job_id,))["n"]
    if n:
        flash(f"Cannot delete “{job['job_title']}”: it has {n} application(s). "
              "Delete those first, or mark the job inactive instead.", "error")
        return redirect(url_for("jobs.detail", job_id=job_id))
    try:
        execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
        flash(f"Job “{job['job_title']}” deleted.", "success")
    except mysql.connector.Error as err:
        flash_db_error(err, "delete job")
        return redirect(url_for("jobs.detail", job_id=job_id))
    return redirect(url_for("jobs.list_jobs"))
