"""CRUD routes for the contacts table."""
import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute, query_all, query_one
from routes import flash_db_error, get_or_404, row_to_form
from validation import validate_contact

bp = Blueprint("contacts", __name__, url_prefix="/contacts")

FIELDS = ["company_id", "first_name", "last_name", "email", "phone", "job_title",
          "linkedin_url", "notes"]

CONTACT_SELECT = """SELECT k.*, c.company_name
                    FROM contacts k JOIN companies c ON c.company_id = k.company_id"""


def _companies():
    return query_all("SELECT company_id, company_name FROM companies ORDER BY company_name")


def _check_company(data, errors):
    if "company_id" not in errors and data.get("company_id") is not None:
        if not query_one("SELECT 1 AS ok FROM companies WHERE company_id = %s", (data["company_id"],)):
            errors["company_id"] = "Please choose an existing company."


def _render_form(form, errors, contact, status=200):
    return render_template("contacts/form.html", form=form, errors=errors, contact=contact,
                           companies=_companies()), status


@bp.route("/")
def list_contacts():
    q = request.args.get("q", "").strip()
    sql, params = CONTACT_SELECT, ()
    if q:
        sql += """ WHERE CONCAT(k.first_name, ' ', k.last_name) LIKE %s
                   OR c.company_name LIKE %s OR k.email LIKE %s OR k.job_title LIKE %s"""
        like = f"%{q}%"
        params = (like, like, like, like)
    sql += " ORDER BY k.last_name, k.first_name"
    return render_template("contacts/list.html", contacts=query_all(sql, params), q=q)


@bp.route("/<int:contact_id>")
def detail(contact_id):
    contact = get_or_404(CONTACT_SELECT + " WHERE k.contact_id = %s", (contact_id,))
    return render_template("contacts/detail.html", contact=contact)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        data, errors = validate_contact(request.form)
        _check_company(data, errors)
        if not errors:
            try:
                new_id, _ = execute(
                    f"INSERT INTO contacts ({', '.join(FIELDS)}) VALUES ({', '.join(['%s'] * len(FIELDS))})",
                    tuple(data[f] for f in FIELDS),
                )
                flash(f"Contact {data['first_name']} {data['last_name']} created.", "success")
                return redirect(url_for("contacts.detail", contact_id=new_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "create contact")
        return _render_form(request.form, errors, None, 400)
    return _render_form({"company_id": request.args.get("company_id", "")}, {}, None)


@bp.route("/<int:contact_id>/edit", methods=["GET", "POST"])
def edit(contact_id):
    contact = get_or_404(CONTACT_SELECT + " WHERE k.contact_id = %s", (contact_id,))
    if request.method == "POST":
        data, errors = validate_contact(request.form)
        _check_company(data, errors)
        if not errors:
            try:
                execute(
                    f"UPDATE contacts SET {', '.join(f + ' = %s' for f in FIELDS)} WHERE contact_id = %s",
                    tuple(data[f] for f in FIELDS) + (contact_id,),
                )
                flash("Contact updated.", "success")
                return redirect(url_for("contacts.detail", contact_id=contact_id))
            except mysql.connector.Error as err:
                flash_db_error(err, "update contact")
        return _render_form(request.form, errors, contact, 400)
    return _render_form(row_to_form(contact), {}, contact)


@bp.route("/<int:contact_id>/delete", methods=["POST"])
def delete(contact_id):
    contact = get_or_404("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
    try:
        execute("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
        flash(f"Contact {contact['first_name']} {contact['last_name']} deleted.", "success")
    except mysql.connector.Error as err:
        flash_db_error(err, "delete contact")
        return redirect(url_for("contacts.detail", contact_id=contact_id))
    return redirect(url_for("contacts.list_contacts"))
