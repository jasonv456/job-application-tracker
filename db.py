"""Database helpers: one MySQL connection per request, stored on flask.g."""
import mysql.connector
from flask import current_app, g


def get_db():
    """Return the connection for the current request, opening it if needed."""
    if "db" not in g:
        cfg = current_app.config
        g.db = mysql.connector.connect(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            database=cfg["DB_NAME"],
        )
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def query_all(sql, params=()):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def query_one(sql, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE, commit, and return (lastrowid, rowcount).

    Rolls back and re-raises on error so callers can show a friendly message.
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid, cur.rowcount
    except mysql.connector.Error:
        conn.rollback()
        raise
    finally:
        cur.close()


def init_app(app):
    app.teardown_appcontext(close_db)
