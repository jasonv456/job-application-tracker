"""Job Tracker - Flask application entry point.

Run with:  python app.py   (then open http://127.0.0.1:4751)
"""
from flask import Flask, render_template

import db
from config import Config
from routes.applications import bp as applications_bp
from routes.companies import bp as companies_bp
from routes.contacts import bp as contacts_bp
from routes.jobs import bp as jobs_bp
from routes.main import bp as main_bp
from routes.match import bp as match_bp


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    db.init_app(app)
    for bp in (main_bp, companies_bp, jobs_bp, applications_bp, contacts_bp, match_bp):
        app.register_blueprint(bp)

    @app.template_filter("money")
    def money(value):
        return f"${value:,.0f}" if value is not None else "—"

    @app.template_filter("options")
    def options(items, value_key=None, label_key=None):
        """Build (value, label) pairs for the select() macro."""
        if value_key is None:
            return [(i, i) for i in items]
        return [(i[value_key], i[label_key]) for i in items]

    @app.template_filter("dash")
    def dash(value):
        return value if value not in (None, "") else "—"

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=4751)
