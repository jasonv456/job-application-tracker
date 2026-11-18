"""Integration tests: every CRUD route for all four tables, plus Job Match.

Runs against the isolated job_tracker_test database (see conftest.py).
"""
import json
from datetime import date, timedelta

import pytest

TOMORROW = (date.today() + timedelta(days=1)).isoformat()


# ---------------------------------------------------------------- dashboard
def test_dashboard_shows_counts(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Dashboard" in html and "Backend Developer" in html


@pytest.mark.parametrize("url", ["/", "/companies/", "/jobs/", "/applications/", "/contacts/",
                                 "/match/", "/companies/new", "/jobs/new", "/applications/new",
                                 "/contacts/new", "/companies/1", "/jobs/1", "/applications/1",
                                 "/contacts/1", "/companies/1/edit", "/jobs/1/edit",
                                 "/applications/1/edit", "/contacts/1/edit"])
def test_every_page_renders(client, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("url", ["/companies/999", "/jobs/999", "/applications/999", "/contacts/999",
                                 "/companies/999/edit", "/jobs/999/edit"])
def test_missing_records_return_404(client, url):
    r = client.get(url)
    assert r.status_code == 404
    assert "doesn't exist" in r.get_data(as_text=True)


# ---------------------------------------------------------------- companies
def test_company_list_and_search(client):
    html = client.get("/companies/?q=glob").get_data(as_text=True)
    assert "Globex" in html and "Acme Corp" not in html


def test_create_company(client, db_row):
    r = client.post("/companies/new", data={"company_name": "Initech", "industry": "Software",
                                            "website": "initech.com", "city": "Dallas"},
                    follow_redirects=True)
    assert r.status_code == 200 and "created" in r.get_data(as_text=True)
    row = db_row("SELECT * FROM companies WHERE company_name = 'Initech'")
    assert row["city"] == "Dallas" and row["state"] is None


def test_create_company_requires_name(client, db_row):
    r = client.post("/companies/new", data={"company_name": "   "})
    assert r.status_code == 400
    assert "Company name is required" in r.get_data(as_text=True)
    assert db_row("SELECT COUNT(*) AS n FROM companies")["n"] == 3


def test_create_company_rejects_bad_website_and_long_name(client):
    r = client.post("/companies/new", data={"company_name": "x" * 101, "website": "not a url"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "at most 100 characters" in html and "Website is not valid" in html


def test_update_company(client, db_row):
    r = client.post("/companies/2/edit", data={"company_name": "Globex Intl", "city": "Houston"},
                    follow_redirects=True)
    assert "Company updated" in r.get_data(as_text=True)
    row = db_row("SELECT * FROM companies WHERE company_id = 2")
    assert row["company_name"] == "Globex Intl" and row["city"] == "Houston"


def test_delete_company_without_children(client, db_row):
    r = client.post("/companies/3/delete", follow_redirects=True)
    assert "deleted" in r.get_data(as_text=True)
    assert db_row("SELECT * FROM companies WHERE company_id = 3") is None


def test_delete_company_with_jobs_is_blocked(client, db_row):
    r = client.post("/companies/1/delete", follow_redirects=True)
    assert "Cannot delete" in r.get_data(as_text=True)
    assert db_row("SELECT * FROM companies WHERE company_id = 1") is not None


def test_delete_requires_post(client):
    assert client.get("/companies/3/delete").status_code == 405


# ---------------------------------------------------------------- jobs
def test_job_list_search_by_title_and_company(client):
    html = client.get("/jobs/?q=frontend").get_data(as_text=True)
    assert "Frontend Developer" in html and "Backend Developer" not in html
    html = client.get("/jobs/?q=globex").get_data(as_text=True)
    assert "Data Analyst" in html and "Backend Developer" not in html


def test_job_search_by_skill_uses_json_column(client):
    html = client.get("/jobs/?q=docker").get_data(as_text=True)
    assert "Backend Developer" in html and "Frontend Developer" not in html


def test_create_job_stores_requirements_as_json(client, db_row):
    r = client.post("/jobs/new", data={
        "company_id": "2", "job_title": "ML Engineer", "requirements": "Python, PyTorch, python, SQL",
        "salary_min": "90000", "salary_max": "120000", "job_type": "Full-time", "is_active": "on",
    }, follow_redirects=True)
    assert "created" in r.get_data(as_text=True)
    row = db_row("SELECT * FROM jobs WHERE job_title = 'ML Engineer'")
    assert json.loads(row["requirements"]) == ["Python", "PyTorch", "SQL"]  # de-duplicated
    assert row["is_active"] == 1 and row["company_id"] == 2


def test_create_job_validation(client):
    r = client.post("/jobs/new", data={"company_id": "", "job_title": "", "salary_min": "100",
                                       "salary_max": "50", "job_type": "Gig", "date_posted": TOMORROW})
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    for msg in ("Company is required", "Job title is required", "Maximum salary must be greater",
                "Job type must be one of", "cannot be in the future"):
        assert msg in html


def test_create_job_rejects_nonexistent_company(client):
    r = client.post("/jobs/new", data={"company_id": "999", "job_title": "Ghost"})
    assert r.status_code == 400 and "existing company" in r.get_data(as_text=True)


def test_create_job_rejects_non_numeric_salary(client):
    r = client.post("/jobs/new", data={"company_id": "1", "job_title": "X", "salary_min": "lots"})
    assert r.status_code == 400 and "must be a number" in r.get_data(as_text=True)


def test_edit_job_form_prefills_requirements(client):
    html = client.get("/jobs/1/edit").get_data(as_text=True)
    assert "Python, SQL, Git, Docker" in html


def test_update_job_and_unchecking_active(client, db_row):
    client.post("/jobs/2/edit", data={"company_id": "1", "job_title": "Frontend Engineer",
                                      "requirements": "React, CSS"})
    row = db_row("SELECT * FROM jobs WHERE job_id = 2")
    assert row["job_title"] == "Frontend Engineer"
    assert json.loads(row["requirements"]) == ["React", "CSS"]
    assert row["is_active"] == 0  # checkbox not sent -> inactive


def test_delete_job_without_applications(client, db_row):
    client.post("/jobs/2/delete")
    assert db_row("SELECT * FROM jobs WHERE job_id = 2") is None


def test_delete_job_with_applications_is_blocked(client, db_row):
    r = client.post("/jobs/1/delete", follow_redirects=True)
    assert "Cannot delete" in r.get_data(as_text=True)
    assert db_row("SELECT * FROM jobs WHERE job_id = 1") is not None


# ---------------------------------------------------------------- applications
def test_application_list_status_filter(client):
    assert "Backend Developer" in client.get("/applications/?status=Applied").get_data(as_text=True)
    assert "No applications found" in client.get("/applications/?status=Rejected").get_data(as_text=True)


def test_new_application_prefills_job_from_query(client):
    html = client.get("/applications/new?job_id=2").get_data(as_text=True)
    assert '<option value="2" selected' in html


def test_create_application(client, db_row):
    r = client.post("/applications/new", data={
        "job_id": "2", "application_date": "2025-02-01", "status": "Phone Screen",
        "resume_version": "v3", "cover_letter_sent": "on", "interview_date": "2025-02-10T14:30",
    }, follow_redirects=True)
    assert "Application created" in r.get_data(as_text=True)
    row = db_row("SELECT * FROM applications WHERE job_id = 2")
    assert row["status"] == "Phone Screen" and row["cover_letter_sent"] == 1
    assert row["interview_date"].hour == 14


def test_create_application_validation(client):
    r = client.post("/applications/new", data={"job_id": "1", "application_date": "2025-02-10",
                                               "status": "Ghosted", "response_date": "2025-02-01"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "Status must be one of" in html and "Response date cannot be before" in html


def test_create_application_requires_job_and_date(client):
    r = client.post("/applications/new", data={"job_id": "", "application_date": "not-a-date"})
    html = r.get_data(as_text=True)
    assert "Job is required" in html and "not a valid date" in html


def test_update_application(client, db_row):
    client.post("/applications/1/edit", data={"job_id": "1", "application_date": "2025-01-10",
                                              "status": "Offer Received", "notes": "Great call"})
    row = db_row("SELECT * FROM applications WHERE application_id = 1")
    assert row["status"] == "Offer Received" and row["notes"] == "Great call"


def test_delete_application(client, db_row):
    client.post("/applications/1/delete")
    assert db_row("SELECT * FROM applications WHERE application_id = 1") is None


# ---------------------------------------------------------------- contacts
def test_contact_search(client):
    assert "Lovelace" in client.get("/contacts/?q=ada").get_data(as_text=True)
    assert "No contacts found" in client.get("/contacts/?q=zzz").get_data(as_text=True)


def test_create_contact(client, db_row):
    r = client.post("/contacts/new", data={"company_id": "2", "first_name": "Grace", "last_name": "Hopper",
                                           "email": "grace@globex.com", "phone": "(305) 555-0100"},
                    follow_redirects=True)
    assert "created" in r.get_data(as_text=True)
    assert db_row("SELECT * FROM contacts WHERE last_name = 'Hopper'")["company_id"] == 2


def test_create_contact_validation(client):
    r = client.post("/contacts/new", data={"company_id": "1", "first_name": "", "last_name": "X",
                                           "email": "bad-email", "phone": "call me"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "First name is required" in html and "Email is not valid" in html and "Phone is not valid" in html


def test_update_contact(client, db_row):
    client.post("/contacts/1/edit", data={"company_id": "2", "first_name": "Ada", "last_name": "King",
                                          "job_title": "CTO"})
    row = db_row("SELECT * FROM contacts WHERE contact_id = 1")
    assert row["last_name"] == "King" and row["company_id"] == 2 and row["email"] is None


def test_delete_contact(client, db_row):
    client.post("/contacts/1/delete")
    assert db_row("SELECT * FROM contacts WHERE contact_id = 1") is None


# ---------------------------------------------------------------- job match
def test_match_page_without_skills_shows_form_only(client):
    html = client.get("/match/").get_data(as_text=True)
    assert "Your skills" in html and "matching job" not in html


def test_match_ranks_jobs_with_percentages(client):
    r = client.post("/match/", data={"skills": "python, sql, html"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    # Backend: 2/4 = 50%, Frontend: 1/3 = 33%, Data Analyst is inactive -> hidden
    assert "50%" in html and "33%" in html
    assert html.index("Backend Developer") < html.index("Frontend Developer")
    assert "Data Analyst" not in html
    assert "1 job(s) have no required skills" in html  # Office Manager


def test_match_full_match_and_zero_match(client):
    html = client.post("/match/", data={"skills": "JS, html, css"},  # JS alias -> JavaScript
                       follow_redirects=True).get_data(as_text=True)
    assert "100%" in html and "0%" in html
    assert html.index("Frontend Developer") < html.index("Backend Developer")


def test_match_remembers_skills_on_job_detail(client):
    client.post("/match/", data={"skills": "Python, Git"})
    html = client.get("/jobs/1").get_data(as_text=True)
    assert "50%" in html and "2 of 4 required skills" in html


def test_match_with_empty_skills_shows_error(client):
    r = client.post("/match/", data={"skills": "  "}, follow_redirects=True)
    assert "Enter at least one skill" in r.get_data(as_text=True)


def test_clear_skills(client):
    client.post("/match/", data={"skills": "Python"})
    r = client.post("/match/clear", follow_redirects=True)
    assert "cleared" in r.get_data(as_text=True)
    with client.session_transaction() as s:
        assert "skills" not in s
