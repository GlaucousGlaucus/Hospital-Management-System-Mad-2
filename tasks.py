from __future__ import annotations

import logging
from calendar import month_name
from datetime import date, datetime, time, timedelta
from uuid import uuid4

from flask import render_template_string
from sqlalchemy.orm import joinedload

from celery_app import celery_app
from models.main_models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    ExportJob,
    ExportJobStatus,
    Patient,
    SessionLocal,
    Treatment,
)
from utils.notifications import ensure_exports_dir, send_email, write_csv
logger = logging.getLogger(__name__)


def _display_time(value: time) -> str:
    return value.strftime("%I:%M %p")


def _monthly_window(today: date | None = None) -> tuple[date, date]:
    anchor = today or date.today()
    first_of_current_month = anchor.replace(day=1)
    last_of_previous_month = first_of_current_month - timedelta(days=1)
    first_of_previous_month = last_of_previous_month.replace(day=1)
    return first_of_previous_month, last_of_previous_month


def _doctor_monthly_report_html(doctor: Doctor, appointments: list[Appointment], period_start: date, period_end: date) -> str:
    return render_template_string(
        """
        <html>
          <body style="font-family: Arial, sans-serif; color: #1f2937;">
            <h2 style="margin-bottom: 4px;">Monthly Activity Report</h2>
            <p style="margin-top: 0;">Doctor: <strong>{{ doctor.name }}</strong></p>
            <p>Reporting window: {{ period_start.strftime("%d %b %Y") }} to {{ period_end.strftime("%d %b %Y") }}</p>
            <p>Total appointments completed: <strong>{{ appointments|length }}</strong></p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
              <thead>
                <tr>
                  <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Patient</th>
                  <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Appointment</th>
                  <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Diagnosis</th>
                  <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Treatment</th>
                  <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Notes</th>
                </tr>
              </thead>
              <tbody>
                {% for appointment in appointments %}
                <tr>
                  <td style="border: 1px solid #d1d5db; padding: 8px;">{{ appointment.patient.name }}</td>
                  <td style="border: 1px solid #d1d5db; padding: 8px;">{{ appointment.date.strftime("%d %b %Y") }} {{ appointment.time.strftime("%I:%M %p") }}</td>
                  <td style="border: 1px solid #d1d5db; padding: 8px;">{{ appointment.treatment.diagnosis if appointment.treatment and appointment.treatment.diagnosis else "-" }}</td>
                  <td style="border: 1px solid #d1d5db; padding: 8px;">{{ appointment.treatment.prescription if appointment.treatment and appointment.treatment.prescription else "-" }}</td>
                  <td style="border: 1px solid #d1d5db; padding: 8px;">{{ appointment.treatment.notes if appointment.treatment and appointment.treatment.notes else "-" }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </body>
        </html>
        """,
        doctor=doctor,
        appointments=appointments,
        period_start=period_start,
        period_end=period_end,
    )


@celery_app.task(name="tasks.generate_daily_summary_report")
def generate_daily_summary_report():
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


@celery_app.task(name="tasks.send_daily_patient_reminders")
def send_daily_patient_reminders():
    today = date.today()
    sent_count = 0
    reminders = []

    with SessionLocal() as db:
        appointments = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor),
            )
            .filter(
                Appointment.date == today,
                Appointment.status == AppointmentStatus.BOOKED,
            )
            .order_by(Appointment.time)
            .all()
        )

        for appointment in appointments:
            patient = appointment.patient
            doctor = appointment.doctor
            subject = f"Hospital visit reminder for {today.strftime('%d %b %Y')}"
            text_body = (
                f"Dear {patient.name},\n\n"
                f"This is a reminder that you have an appointment with Dr. {doctor.name} "
                f"today at {_display_time(appointment.time)}.\n"
                f"Visit type: {appointment.visit_type or 'General consultation'}.\n\n"
                "Please arrive on time."
            )
            html_body = (
                f"<p>Dear {patient.name},</p>"
                f"<p>This is a reminder that you have an appointment with <strong>Dr. {doctor.name}</strong> "
                f"today at <strong>{_display_time(appointment.time)}</strong>.</p>"
                f"<p>Visit type: {appointment.visit_type or 'General consultation'}.</p>"
                "<p>Please arrive on time.</p>"
            )

            delivered_channels = []
            try:
                logger.info(f"Sending reminder for appointment: {patient.name}")
                if send_email(subject, [patient.email], text_body, html_body):
                    delivered_channels.append("email")
            except Exception as e:
                logger.exception(e)

            reminders.append({
                "appointment_id": appointment.id,
                "patient_id": patient.id,
                "patient_name": patient.name,
                "channels": delivered_channels or ["none_configured"],
            })
            if delivered_channels:
                sent_count += 1

    return {
        "date": today.isoformat(),
        "appointments_considered": len(reminders),
        "notifications_sent": sent_count,
        "reminders": reminders,
    }


@celery_app.task(name="tasks.send_monthly_doctor_activity_reports")
def send_monthly_doctor_activity_reports():
    period_start, period_end = _monthly_window()
    sent = 0
    reports = []

    with SessionLocal() as db:
        doctors = db.query(Doctor).order_by(Doctor.name).all()

        for doctor in doctors:
            appointments = (
                db.query(Appointment)
                .options(
                    joinedload(Appointment.patient),
                    joinedload(Appointment.treatment).joinedload(Treatment.medicines),
                )
                .filter(
                    Appointment.doctor_id == doctor.id,
                    Appointment.status == AppointmentStatus.COMPLETED,
                    Appointment.date >= period_start,
                    Appointment.date <= period_end,
                )
                .order_by(Appointment.date, Appointment.time)
                .all()
            )

            html_body = _doctor_monthly_report_html(doctor, appointments, period_start, period_end)
            month_label = f"{month_name[period_start.month]} {period_start.year}"
            text_body = (
                f"Monthly activity report for Dr. {doctor.name}\n"
                f"Period: {period_start.isoformat()} to {period_end.isoformat()}\n"
                f"Completed appointments: {len(appointments)}"
            )
            try:
                delivered = send_email(
                    subject=f"Monthly activity report - {month_label}",
                    recipients=[doctor.email],
                    text_body=text_body,
                    html_body=html_body,
                )
            except Exception:
                delivered = False
            reports.append({
                "doctor_id": doctor.id,
                "doctor_name": doctor.name,
                "doctor_email": doctor.email,
                "appointments": len(appointments),
                "delivered": delivered,
            })
            if delivered:
                sent += 1

    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "reports_generated": len(reports),
        "reports_delivered": sent,
        "items": reports,
    }


@celery_app.task(bind=True, name="tasks.generate_patient_treatment_csv_export")
def generate_patient_treatment_csv_export(self, export_job_id: int):
    with SessionLocal() as db:
        export_job = (
            db.query(ExportJob)
            .options(
                joinedload(ExportJob.patient)
                .joinedload(Patient.appointments)
                .joinedload(Appointment.doctor),
                joinedload(ExportJob.patient)
                .joinedload(Patient.appointments)
                .joinedload(Appointment.treatment)
                .joinedload(Treatment.medicines),
            )
            .get(export_job_id)
        )
        if not export_job:
            raise ValueError(f"Export job {export_job_id} not found.")

        export_job.task_id = self.request.id
        export_job.status = ExportJobStatus.PROCESSING
        db.commit()

        patient = export_job.patient
        rows = []
        for appointment in sorted(patient.appointments, key=lambda item: (item.date, item.time)):
            treatment = appointment.treatment
            medicine_summary = ", ".join(
                f"{medicine.name} ({medicine.duration_days}d)"
                for medicine in (treatment.medicines if treatment else [])
            )
            rows.append([
                str(patient.id),
                patient.name,
                appointment.doctor.name if appointment.doctor else "",
                appointment.date.isoformat(),
                appointment.time.isoformat(timespec="minutes"),
                appointment.status.value,
                appointment.visit_type or "",
                treatment.diagnosis if treatment and treatment.diagnosis else "",
                treatment.prescription if treatment and treatment.prescription else "",
                treatment.notes if treatment and treatment.notes else "",
                medicine_summary,
                appointment.original_date.isoformat() if appointment.original_date else "",
                appointment.original_time.isoformat(timespec="minutes") if appointment.original_time else "",
            ])

        exports_dir = ensure_exports_dir()
        file_name = f"patient-{patient.id}-treatments-{uuid4().hex[:8]}.csv"
        file_path = exports_dir / file_name
        write_csv(
            file_path,
            headers=[
                "user_id",
                "username",
                "consulting_doctor",
                "appointment_date",
                "appointment_time",
                "appointment_status",
                "visit_type",
                "diagnosis",
                "treatment_given",
                "doctor_notes",
                "medicines",
                "next_visit_suggested_date",
                "next_visit_suggested_time",
            ],
            rows=rows,
        )

        export_job.status = ExportJobStatus.COMPLETED
        export_job.file_name = file_name
        export_job.file_path = str(file_path)
        export_job.completed_at = datetime.utcnow()
        export_job.error_message = None
        db.commit()

        subject = "Your treatment CSV export is ready"
        text_body = f"Hello {patient.name}, your treatment export has been generated successfully."
        try:
            send_email(subject, [patient.email], text_body)
        except Exception:
            pass

        return {
            "export_job_id": export_job.id,
            "patient_id": patient.id,
            "file_name": file_name,
            "completed_at": export_job.completed_at.isoformat(),
        }
