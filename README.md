# Job Tracker (Flask + MySQL)

A simple web app to track a job search: companies, job postings, applications and
contacts, plus a **Job Match** page that shows what percentage of each job's
required skills you have.

## Features

- **Full CRUD** (list, view, create, edit, delete) for all four tables:
  `companies`, `jobs`, `applications`, `contacts`
- **Validation** on every form (required fields, max lengths, email/phone/URL
  formats, numbers, dates, salary min ≤ max, allowed status/job-type values,
  foreign key must exist). Errors are shown next to each field.
- **Safe deletes**: a company with jobs/contacts, or a job with applications,
  cannot be deleted (protects the foreign keys). Every delete asks for confirmation.
- **Search** on every list page (jobs can also be searched by skill).
- **Job Match**: enter your skills and every active job is ranked by
  `matched required skills ÷ total required skills × 100`, showing the skills you
  have and the ones you're missing. Your skills are remembered for the session,
  so each job's detail page shows your match too.

## Database

Database `job_tracker` (MySQL 8):

| Table          | Key columns                                   | Relationship                         |
|----------------|-----------------------------------------------|--------------------------------------|
| `companies`    | company_id (PK), company_name, industry, …    | parent of jobs and contacts          |
| `jobs`         | job_id (PK), company_id (FK), **requirements (JSON)**, salary_min/max, … | `company_id → companies` |
| `applications` | application_id (PK), job_id (FK), status, …   | `job_id → jobs`                      |
| `contacts`     | contact_id (PK), company_id (FK), name, email | `company_id → companies`             |

`jobs.requirements` is a **JSON array** of skills, e.g. `["Python", "SQL", "Git"]`.
It was added by `db/migration_add_requirements.sql`, which also fills it in for
the 18 sample jobs. `db/schema.sql` is the full schema.

## Setup

```powershell
cd C:\Users\jason\Desktop\vs\python\job_tracker_app
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# one-time: add the JSON column (safe to re-run)
Get-Content db\migration_add_requirements.sql -Raw | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -uroot -p

.\.venv\Scripts\python app.py
```

Open <http://127.0.0.1:4751>. MySQL (service `MySQL80`) must be running.

The database login defaults to `root` / `root`. To use different credentials, set
environment variables before starting the app: `DB_HOST`, `DB_USER`, `DB_PASSWORD`,
`DB_NAME`, `SECRET_KEY`.

## Tests

```powershell
.\.venv\Scripts\python -m pytest -v
```

74 tests: unit tests for the match calculation (`tests/test_matching.py`) and
integration tests for every page and every CRUD route (`tests/test_routes.py`).
The tests create and drop their own `job_tracker_test` database, so your real
data is never touched.

## Project structure

```
app.py              app factory, template filters, error pages
config.py           settings (env-var overridable)
db.py               per-request MySQL connection + query helpers
matching.py         Job Match logic (pure functions)
validation.py       form validation for all four tables
routes/             one blueprint per table + main (dashboard) + match
templates/          Jinja templates (base layout, shared form macros, pages)
static/style.css    stylesheet
db/                 schema.sql and migration
tests/              pytest suite
AI_USAGE.md         how generative AI was used
```
