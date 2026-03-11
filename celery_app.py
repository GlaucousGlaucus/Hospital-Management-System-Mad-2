from __future__ import annotations

import os
from celery import Celery

from app import create_app
from config import get_config


def make_celery(flask_app) -> Celery:
    """Create a Celery instance bound to the Flask app context."""
    config = get_config()

    celery = Celery(
        flask_app.import_name,
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
    )

    celery.conf.update(
        timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
        enable_utc=True,
    )

    class ContextTask(celery.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery


flask_app = create_app()
celery_app = make_celery(flask_app)

