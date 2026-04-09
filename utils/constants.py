from pathlib import Path

__content_root_path__ = Path(__file__).parent
DB_PATH = __content_root_path__.parent / "hospital.db"

class UserTypes:
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"

class SessionInfo:
    USER_ID = "user_id"
    USER_NAME = "user_name"
    USER_EMAIL = "user_email"
    USER_TYPE = "user_type"
