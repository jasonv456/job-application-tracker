"""Dashboard / home page."""
from flask import Blueprint, render_template

from db import query_all, query_one

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    counts = query_one(
        """SELECT (SELECT COUNT(*) FROM companies)    AS companies,
                  (SELECT COUNT(*) FROM jobs WHERE is_active = 1) AS active_jobs,
                  (SELECT COUNT(*) FROM jobs)         AS jobs,
                  (SELECT COUNT(*) FROM applications) AS applications,
                  (SELECT COUNT(*) FROM contacts)     AS contacts"""
    )
    by_status = query_all(
        "SELECT status, COUNT(*) AS n FROM applications GROUP BY status ORDER BY n DESC, status"
    )
    recent = query_all(
        """SELECT a.application_id, a.application_date, a.status,
                  j.job_id, j.job_title, c.company_id, c.company_name
           FROM applications a
           JOIN jobs j ON j.job_id = a.job_id
           JOIN companies c ON c.company_id = j.company_id
           ORDER BY a.application_date DESC, a.application_id DESC
           LIMIT 5"""
    )
    return render_template("index.html", counts=counts, by_status=by_status, recent=recent)
