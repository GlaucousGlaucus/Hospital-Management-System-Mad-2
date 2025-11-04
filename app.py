from logging import getLogger
from flask import Flask, render_template

import models.main_models as db_util

logger = getLogger(__name__)

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "SECRET"
    # app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    db_util.setup_db()

    from routes.auth import auth_login_bp, auth_signup_bp
    from routes.dashboard import dashboard_bp, admin_bp, doctor_bp
    from routes.api_routes import api_bp
    app.register_blueprint(auth_signup_bp)
    app.register_blueprint(auth_login_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """
        Ensure the session is closed after each request.
        We don't want to leave any sessions open otherwise bad things can happen.
        """
        db_util.SessionLocal.remove()

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
