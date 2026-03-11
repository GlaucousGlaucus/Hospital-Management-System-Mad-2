from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab

from app import create_app
from config import get_config


def make_celery(flask_app) -> Celery:
    """Create a Celery instance bound to the Flask app context."""
    config = get_config()

    celery = Celery(
        flask_app.import_name,
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
        include=["tasks"],
    )

    celery.conf.update(
        timezone=os.getenv("CELERY_TIMEZONE", config.CELERY_TIMEZONE),
        enable_utc=False,
        beat_schedule={
            "daily-patient-reminders": {
                "task": "tasks.send_daily_patient_reminders",
                "schedule": crontab(
                    hour=config.DAILY_REMINDER_HOUR,
                    minute=config.DAILY_REMINDER_MINUTE,
                ),
            },
            "monthly-doctor-activity-reports": {
                "task": "tasks.send_monthly_doctor_activity_reports",
                "schedule": crontab(
                    day_of_month=1,
                    hour=config.MONTHLY_REPORT_HOUR,
                    minute=config.MONTHLY_REPORT_MINUTE,
                ),
            },
        },
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
