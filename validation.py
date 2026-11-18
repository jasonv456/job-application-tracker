"""Server-side form validation shared by all CRUD routes.

Each validate_* function takes request.form and returns (clean_data, errors),
where errors maps field name -> message. Empty optional fields become None.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from matching import parse_skills

APPLICATION_STATUSES = [
    "Applied", "Phone Screen", "Interview Scheduled", "Interview Completed",
    "Offer Received", "Offer Accepted", "Rejected", "Withdrawn",
]
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship", "Temporary"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL_RE = re.compile(r"^(https?://)?([\w-]+\.)+[\w-]{2,}(/\S*)?$", re.IGNORECASE)
PHONE_RE = re.compile(r"^[\d\s()+.\-]{7,20}$")


class Validator:
    def __init__(self, form):
        self.form = form
        self.data = {}
        self.errors = {}

    def _raw(self, field):
        value = self.form.get(field, "")
        return value.strip() if isinstance(value, str) else value

    def text(self, field, label, required=False, max_len=None):
        value = self._raw(field)
        if not value:
            if required:
                self.errors[field] = f"{label} is required."
            self.data[field] = None
            return
        if max_len and len(value) > max_len:
            self.errors[field] = f"{label} must be at most {max_len} characters."
        self.data[field] = value

    def pattern(self, field, label, regex, max_len=None, hint=""):
        self.text(field, label, max_len=max_len)
        value = self.data[field]
        if value and field not in self.errors and not regex.match(value):
            self.errors[field] = f"{label} is not valid.{(' ' + hint) if hint else ''}"

    def integer(self, field, label, required=False):
        value = self._raw(field)
        if not value:
            if required:
                self.errors[field] = f"{label} is required."
            self.data[field] = None
            return
        try:
            self.data[field] = int(value)
        except ValueError:
            self.errors[field] = f"{label} must be a whole number."
            self.data[field] = None

    def money(self, field, label):
        value = self._raw(field).replace(",", "").replace("$", "") if self._raw(field) else ""
        if not value:
            self.data[field] = None
            return
        try:
            amount = Decimal(value)
        except InvalidOperation:
            self.errors[field] = f"{label} must be a number."
            self.data[field] = None
            return
        if amount < 0 or amount >= Decimal("100000000"):
            self.errors[field] = f"{label} must be between 0 and 99,999,999."
        self.data[field] = amount

    def date(self, field, label, required=False, fmt="%Y-%m-%d"):
        value = self._raw(field)
        if not value:
            if required:
                self.errors[field] = f"{label} is required."
            self.data[field] = None
            return
        try:
            parsed = datetime.strptime(value, fmt)
            self.data[field] = parsed.date() if fmt == "%Y-%m-%d" else parsed
        except ValueError:
            self.errors[field] = f"{label} is not a valid date."
            self.data[field] = None

    def choice(self, field, label, choices, required=False, default=None):
        value = self._raw(field) or default
        if not value:
            if required:
                self.errors[field] = f"{label} is required."
            self.data[field] = None
            return
        if value not in choices:
            self.errors[field] = f"{label} must be one of: {', '.join(choices)}."
        self.data[field] = value

    def checkbox(self, field):
        self.data[field] = 1 if self.form.get(field) in ("on", "1", "true", "yes") else 0

    def result(self):
        return self.data, self.errors


def validate_company(form):
    v = Validator(form)
    v.text("company_name", "Company name", required=True, max_len=100)
    v.text("industry", "Industry", max_len=50)
    v.pattern("website", "Website", URL_RE, max_len=200, hint="Example: www.example.com")
    v.text("city", "City", max_len=50)
    v.text("state", "State", max_len=50)
    v.text("notes", "Notes", max_len=5000)
    return v.result()


def validate_job(form):
    v = Validator(form)
    v.integer("company_id", "Company", required=True)
    v.text("job_title", "Job title", required=True, max_len=100)
    v.text("job_description", "Description", max_len=10000)
    v.money("salary_min", "Minimum salary")
    v.money("salary_max", "Maximum salary")
    v.choice("job_type", "Job type", JOB_TYPES)
    v.pattern("posting_url", "Posting URL", URL_RE, max_len=500)
    v.date("date_posted", "Date posted")
    v.checkbox("is_active")
    data, errors = v.result()

    lo, hi = data.get("salary_min"), data.get("salary_max")
    if lo is not None and hi is not None and lo > hi and "salary_max" not in errors:
        errors["salary_max"] = "Maximum salary must be greater than or equal to the minimum."
    if data.get("date_posted") and data["date_posted"] > date.today():
        errors["date_posted"] = "Date posted cannot be in the future."

    skills = parse_skills(form.get("requirements", ""))
    if len(skills) > 50:
        errors["requirements"] = "Please list at most 50 skills."
    elif any(len(s) > 60 for s in skills):
        errors["requirements"] = "Each skill must be at most 60 characters."
    data["requirements"] = skills
    return data, errors


def validate_application(form):
    v = Validator(form)
    v.integer("job_id", "Job", required=True)
    v.date("application_date", "Application date", required=True)
    v.choice("status", "Status", APPLICATION_STATUSES, default="Applied")
    v.text("resume_version", "Resume version", max_len=50)
    v.checkbox("cover_letter_sent")
    v.date("response_date", "Response date")
    v.date("interview_date", "Interview date", fmt="%Y-%m-%dT%H:%M")
    v.text("notes", "Notes", max_len=5000)
    data, errors = v.result()

    applied = data.get("application_date")
    if applied and applied > date.today():
        errors["application_date"] = "Application date cannot be in the future."
    if applied and data.get("response_date") and data["response_date"] < applied:
        errors["response_date"] = "Response date cannot be before the application date."
    if applied and data.get("interview_date") and data["interview_date"].date() < applied:
        errors["interview_date"] = "Interview date cannot be before the application date."
    return data, errors


def validate_contact(form):
    v = Validator(form)
    v.integer("company_id", "Company", required=True)
    v.text("first_name", "First name", required=True, max_len=50)
    v.text("last_name", "Last name", required=True, max_len=50)
    v.pattern("email", "Email", EMAIL_RE, max_len=100, hint="Example: name@company.com")
    v.pattern("phone", "Phone", PHONE_RE, max_len=20, hint="Use digits, spaces, ( ) + - only.")
    v.text("job_title", "Job title", max_len=100)
    v.pattern("linkedin_url", "LinkedIn URL", URL_RE, max_len=200)
    v.text("notes", "Notes", max_len=5000)
    return v.result()
