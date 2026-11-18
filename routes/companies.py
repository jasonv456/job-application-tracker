"""CRUD routes for the companies table."""
import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute, query_all, query_one
from routes import flash_db_error, get_or_404, row_to_form
from validation import validate_company

bp = Blueprint("companies", __name__, url_prefix="/companies")

FIELDS = ["company_name", "industry", "website", "city", "state", "notes"]


@bp.route("/")
def list_companies():
    q = request.args.get("q", "").strip()
    sql = """SELECT c.*,
                    (SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.company_id)     AS job_count,
                    (SELECT COUNT(*) FROM contacts k WHERE k.company_id = c.company_id) AS contact_count
             FROM companies c"""
    params = ()
    if q:
        sql += " WHERE c.company_name LIKE %s OR c.industry LIKE %s OR c.city LIKE %s"
        like = f"%{q}%"
        params = (like, like, like)
    sql += " ORDER BY c.company_name"
    return render_template("companies/list.html", companies=query_all(sql, params), q=q)


@bp.route("/<int:company_id>")
def detail(company_id):
    company = get_or_404("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    jobs = query_all(
        "SELECT * FROM jobs WHERE company_id = %s ORDER BY is_active DESC, job_title", (company_id,)
    )
    contacts = query_all(
        "SELECT * FROM contacts WHERE company_id = %s ORDER BY last_name, first_name", (company_id,)
    )
    return render_template("companies/detail.html", company=company, jobs=jobs, contacts=contacts)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        data, errors = validate_company(request.form)
        if not errors:
            try:
                new_id, _ = execute(
                    f"INSERT INTO companies ({', '.join(FIELDS)}) VALUES ({', '.join(['%s'] * len(FIELDS))})",
                    tuple(data[f] for f in FIELDS),
                )
                flash(f"Company “{data['company_name']}” created.", "success")
                return redirect(url_for("companies.detail", company_id=new_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "create company")
        return render_template("companies/form.html", form=request.form, errors=errors, company=None), 400
    return render_template("companies/form.html", form={}, errors={}, company=None)


@bp.route("/<int:company_id>/edit", methods=["GET", "POST"])
def edit(company_id):
    company = get_or_404("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    if request.method == "POST":
        data, errors = validate_company(request.form)
        if not errors:
            try:
                execute(
                    f"UPDATE companies SET {', '.join(f + ' = %s' for f in FIELDS)} WHERE company_id = %s",
                    tuple(data[f] for f in FIELDS) + (company_id,),
                )
                flash("Company updated.", "success")
                return redirect(url_for("companies.detail", company_id=company_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "update company")
        return render_template("companies/form.html", form=request.form, errors=errors, company=company), 400
    return render_template("companies/form.html", form=row_to_form(company), errors={}, company=company)


@bp.route("/<int:company_id>/delete", methods=["POST"])
def delete(company_id):
    company = get_or_404("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    deps = query_one(
        """SELECT (SELECT COUNT(*) FROM jobs WHERE company_id = %s)     AS jobs,
                  (SELECT COUNT(*) FROM contacts WHERE company_id = %s) AS contacts""",
        (company_id, company_id),
    )
    if deps["jobs"] or deps["contacts"]:
        flash(
            f"Cannot delete “{company['company_name']}”: it still has {deps['jobs']} job(s) and "
            f"{deps['contacts']} contact(s). Delete or reassign those first.",
            "error",
        )
        return redirect(url_for("companies.detail", company_id=company_id))
    try:
        execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
        flash(f"Company “{company['company_name']}” deleted.", "success")
    except mysql.connector.Error as err:
        flash_db_error(err, "delete company")
        return redirect(url_for("companies.detail", company_id=company_id))
    return redirect(url_for("companies.list_companies"))
