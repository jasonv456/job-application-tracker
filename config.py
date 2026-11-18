"""Application configuration.

Values can be overridden with environment variables so credentials do not
have to be edited in source code (e.g. `set DB_PASSWORD=secret`).
"""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "root")
    DB_NAME = os.environ.get("DB_NAME", "job_tracker")
