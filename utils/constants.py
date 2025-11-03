from pathlib import Path

__content_root_path__ = Path(__file__).parent
TEMPLATES_PATH = __content_root_path__ / 'templates'
STATIC_PATH = __content_root_path__ / 'static'
DB_PATH = __content_root_path__.parent / "hospital.db"

class Routes:
    LOGIN_ROUTE = "auth_login.login"
    SIGNUP_ROUTE = "auth_signup.signup"
    DASHBOARD_ROUTE = "dashboard.dashboard"

class UserTypes:
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"

class SessionInfo:
    USER_ID = "user_id"
    USER_NAME = "user_name"
    USER_EMAIL = "user_email"
    USER_TYPE = "user_type"
