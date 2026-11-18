"""Pytest fixtures.

Tests never touch the real `job_tracker` database: they build an isolated
`job_tracker_test` database from db/schema.sql and re-seed it before every test.
"""
import json
import os
import sys
from pathlib import Path

import mysql.connector
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from config import Config  # noqa: E402

TEST_DB = os.environ.get("TEST_DB_NAME", "job_tracker_test")


def _server_conn(database=None):
    return mysql.connector.connect(host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
                                   password=Config.DB_PASSWORD, database=database)


@pytest.fixture(scope="session", autouse=True)
def test_database():
    conn = _server_conn()
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS `{TEST_DB}`")
    cur.execute(f"CREATE DATABASE `{TEST_DB}`")
    cur.execute(f"USE `{TEST_DB}`")
    for stmt in (ROOT / "db" / "schema.sql").read_text(encoding="utf-8").split(";"):
        if stmt.strip():
            cur.execute(stmt)
    conn.commit()
    cur.close()
    conn.close()
    yield
    conn = _server_conn()
    conn.cursor().execute(f"DROP DATABASE IF EXISTS `{TEST_DB}`")
    conn.close()


SEED = [
    "INSERT INTO companies (company_id, company_name, industry, website, city, state) VALUES "
    "(1, 'Acme Corp', 'Technology', 'www.acme.com', 'Miami', 'Florida'),"
    "(2, 'Globex', 'Data Science', NULL, 'Austin', 'Texas'),"
    "(3, 'Empty Co', NULL, NULL, NULL, NULL)",
    ("INSERT INTO jobs (job_id, company_id, job_title, requirements, salary_min, salary_max, job_type, is_active) VALUES "
     "(1, 1, 'Backend Developer', %s, 80000, 100000, 'Full-time', 1),"
     "(2, 1, 'Frontend Developer', %s, 70000, 90000, 'Full-time', 1),"
     "(3, 2, 'Data Analyst', %s, 60000, 80000, 'Full-time', 0),"
     "(4, 2, 'Office Manager', NULL, 50000, 60000, 'Part-time', 1)",
     (json.dumps(["Python", "SQL", "Git", "Docker"]),
      json.dumps(["JavaScript", "HTML", "CSS"]),
      json.dumps(["Python", "SQL"]))),
    "INSERT INTO applications (application_id, job_id, application_date, status) VALUES (1, 1, '2025-01-10', 'Applied')",
    "INSERT INTO contacts (contact_id, company_id, first_name, last_name, email) VALUES "
    "(1, 1, 'Ada', 'Lovelace', 'ada@acme.com')",
]


@pytest.fixture(autouse=True)
def seed(test_database):
    conn = _server_conn(TEST_DB)
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ("applications", "contacts", "jobs", "companies"):
        cur.execute(f"TRUNCATE TABLE {table}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    for item in SEED:
        sql, params = item if isinstance(item, tuple) else (item, ())
        cur.execute(sql, params)
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture
def app():
    return create_app({"TESTING": True, "DB_NAME": TEST_DB, "SECRET_KEY": "test"})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_row():
    """Fetch a single row from the test DB (bypassing the app) to verify writes."""
    def _fetch(sql, params=()):
        conn = _server_conn(TEST_DB)
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    return _fetch
