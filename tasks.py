from __future__ import annotations

from datetime import date

from celery_app import celery_app
from models.main_models import Appointment, AppointmentStatus, Doctor, Patient, SessionLocal


@celery_app.task(name="tasks.generate_daily_summary_report")
def generate_daily_summary_report():
    """Generate a simple operational summary for the current day."""
    today = date.today()
    with SessionLocal() as db:
        total_doctors = db.query(Doctor).count()
        total_patients = db.query(Patient).count()
        today_appointments = db.query(Appointment).filter(Appointment.date == today).count()
        booked = db.query(Appointment).filter(
            Appointment.date == today,
            Appointment.status == AppointmentStatus.BOOKED,
        ).count()
        completed = db.query(Appointment).filter(
            Appointment.date == today,
            Appointment.status == AppointmentStatus.COMPLETED,
        ).count()
        cancelled = db.query(Appointment).filter(
            Appointment.date == today,
            Appointment.status == AppointmentStatus.CANCELLED,
        ).count()

    return {
        "generated_for": today.isoformat(),
        "totals": {
            "doctors": total_doctors,
            "patients": total_patients,
            "appointments_today": today_appointments,
        },
        "statuses": {
            "booked": booked,
            "completed": completed,
            "cancelled": cancelled,
        },
    }
