from flask import Flask, abort, render_template

import models.main_models as db_util
from config import get_config
from utils.setup import setup_db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())

    setup_db()

    from routes.auth import auth_api_bp, auth_login_bp
    from routes.api_routes import api_bp

    for blueprint in (
        auth_login_bp,
        auth_api_bp,
        api_bp,
    ):
        app.register_blueprint(blueprint)

    @app.teardown_appcontext
    def shutdown_session(_exception=None):
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
