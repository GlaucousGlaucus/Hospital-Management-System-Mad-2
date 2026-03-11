import os


class BaseConfig:
    """Base application configuration."""

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "SECRET")

    # SQLite (existing behaviour) – path is still controlled via utils.constants.DB_PATH
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///hospital.db",
    )

    # Redis / Celery
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)


def get_config():
    return BaseConfig()

