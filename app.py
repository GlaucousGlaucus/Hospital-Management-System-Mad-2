from logging import getLogger

from flask import Flask, abort, render_template

import models.main_models as db_util
from config import get_config
from utils.setup import setup_db

logger = getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())

    setup_db()

    from routes.auth import auth_api_bp, auth_login_bp, auth_signup_bp
    from routes.dashboard import dashboard_bp, admin_bp, doctor_bp
    from routes.api_routes import api_bp

    app.register_blueprint(auth_signup_bp)
    app.register_blueprint(auth_login_bp)
    app.register_blueprint(auth_api_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    from routes.dashboard import patient_bp
    app.register_blueprint(patient_bp)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """
        Ensure the session is closed after each request.
        We don't want to leave any sessions open otherwise bad things can happen.
        """
        db_util.SessionLocal.remove()

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/<path:path>")
    def spa_entry(path: str):
        if path.startswith("api/") or path.startswith("static/"):
            abort(404)
        return render_template("index.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
