"""Job Match feature: rank active jobs by how many required skills you have."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import query_all
from matching import normalize_skill, parse_skills, rank_jobs

bp = Blueprint("match", __name__, url_prefix="/match")


def _all_known_skills(jobs):
    """Every distinct skill mentioned by any job, shown as a hint under the input."""
    seen = {}
    for job in jobs:
        for skill in parse_skills(job.get("requirements")):
            seen.setdefault(normalize_skill(skill), skill)
    return sorted(seen.values(), key=str.lower)


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        skills = parse_skills(request.form.get("skills", ""))
        if skills:
            session["skills"] = skills
        else:
            session.pop("skills", None)
            flash("Enter at least one skill to see job matches.", "error")
        return redirect(url_for("match.index"))

    skills = session.get("skills", [])
    jobs = query_all(
        """SELECT j.job_id, j.job_title, j.requirements, c.company_id, c.company_name
           FROM jobs j JOIN companies c ON c.company_id = j.company_id
           WHERE j.is_active = 1"""
    )
    results = rank_jobs(skills, jobs) if skills else []
    return render_template("match.html", skills=skills, results=results,
                           known_skills=_all_known_skills(jobs),
                           unscored=sum(1 for j in jobs if not parse_skills(j.get("requirements"))))


@bp.route("/clear", methods=["POST"])
def clear():
    session.pop("skills", None)
    flash("Your skills were cleared.", "success")
    return redirect(url_for("match.index"))
