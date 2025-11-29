import datetime
from logging import getLogger
from typing import List, dataclass_transform

from flask import Blueprint, jsonify, abort, render_template, flash, redirect, url_for, request, session
from sqlalchemy.orm import joinedload

from models.main_models import Doctor, Patient, SessionLocal, Appointment, DoctorAvailability, AppointmentStatus
from utils.constants import SessionInfo, UserTypes

logger = getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/<entity>/all", methods=["GET"])
def get_all_items(entity):
    with SessionLocal() as db_session:
        model_map = {
            "doctors": Doctor,
            "patients": Patient,
            "appointments": Appointment,
        }
        model = model_map.get(entity)

        if not model:
            return jsonify({"error": "Invalid entity"}), 400

        entities = db_session.query(model).all()
        if not entities:
            return jsonify({"error": "Not found"})
        match entity:
            case "doctors":
                data = [
                    {"id": d.id, "name": d.name, "age": d.age, "email": d.email, "contact": d.contact, "specialization": d.specialization or ""}
                    for d in entities
                ]
            case "patients":
                data = [
                    {"id": p.id, "name": p.name, "age": p.age, "email": p.email, "contact": p.contact}
                    for p in entities
                ]
            case "appointments":
                entities: List[Appointment] = entities
                data = [
                    {
                        "id": app.id,
                        "patient_name": app.patient.name,
                        "doctor_name": app.doctor.name,
                        "doctor_dep": app.doctor.department.name,
                        "patient_id": app.patient.id,
                    }
                    for app in entities
                ]
    return jsonify(data)

@api_bp.route("/<entity>/<int:item_id>", methods=["DELETE"])
def delete_item(entity, item_id):
    with SessionLocal() as db_session:
        model_map = {"doctor": Doctor, "patient": Patient}
        model = model_map.get(entity)

        if not model:
            return jsonify({"error": "Invalid entity"}), 400

        item = db_session.get(model, item_id)
        if not item:
            return jsonify({"error": "Not found"}), 404

        db_session.delete(item)
        db_session.commit()
    return jsonify({"status": "deleted"})


@api_bp.route("patient/<int:patient_id>/history")
def patient_history(patient_id: int):
    """Show the patient history table."""
    with SessionLocal() as session:
        patient = (
            session.query(Patient)
            .options(
                joinedload(Patient.appointments)
                .joinedload(Appointment.treatment),
                joinedload(Patient.appointments)
                .joinedload(Appointment.doctor)
                .joinedload(Doctor.department)
            )
            .filter(Patient.id == patient_id)
            .first()
        )

        if not patient:
            abort(404, description="Patient not found")

        # For simplicity, assume all appointments are with the same doctor & department (like your example)
        doctor = patient.appointments[0].doctor if patient.appointments else None
        department = doctor.department if doctor and doctor.department else None

        # Build visit history
        visits = []
        for idx, appt in enumerate(patient.appointments, start=1):
            t = appt.treatment
            visits.append({
                "no": idx,
                "visit_type": appt.visit_type if appt.visit_type else "N/A",
                "tests_done": appt.test_done if appt.test_done else "N/A",
                "diagnosis": t.diagnosis if t else "N/A",
                "prescription": t.prescription if t else "N/A",
                "medicines": t.notes if t else "N/A",
            })

        return render_template(
            "dashboard/patient_history.html",
            patient=patient,
            doctor=doctor,
            department=department,
            visits=visits,
        )

@api_bp.route("doctor/appointment/<int:appointment_id>/complete", methods=["POST"])
def mark_complete(appointment_id):
    with SessionLocal() as db_session:
        appt = db_session.query(Appointment).get(appointment_id)
        appt.status = AppointmentStatus.COMPLETED
        db_session.commit()
    flash("Appointment marked as complete!", "success")
    return redirect(url_for("dashboard.dashboard"))


@api_bp.route("appointment/<int:appointment_id>/cancel", methods=["POST"])
def cancel_appointment(appointment_id):
    with SessionLocal() as db_session:
        appt = db_session.query(Appointment).get(appointment_id)
        appt.status = AppointmentStatus.CANCELLED
        db_session.commit()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("dashboard.dashboard"))


@api_bp.route("appointment/<int:appointment_id>/reschedule", methods=["POST"])
def reschedule_appointment(appointment_id):
    data = request.get_json()

    new_date_str = data.get("new_date")
    new_time_str = data.get("new_time")

    if not new_date_str or not new_time_str:
        return jsonify({"error": "Missing new date or time"}), 400

    try:
        new_date = datetime.date.fromisoformat(new_date_str)
        new_time = datetime.time.fromisoformat(new_time_str)
    except ValueError:
        return jsonify({"error": "Invalid date/time format"}), 400

    with SessionLocal() as db_session:
        appointment = db_session.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        conflict = db_session.query(Appointment).filter_by(
            doctor_id=appointment.doctor_id,
            date=new_date,
            time=new_time
        ).first()

        if conflict:
            return jsonify({"error": "Slot already booked"}), 409

        if appointment.reschedule_count == 0:
            appointment.original_date = appointment.date
            appointment.original_time = appointment.time

        appointment.date = new_date
        appointment.time = new_time
        appointment.reschedule_count += 1

        appointment.status = AppointmentStatus.BOOKED

        db_session.commit()

    flash("Appointment rescheduled successfully!", "success")
    return jsonify({"status": "success"})

@api_bp.route("doctor/update_availability", methods=["POST"])
def update_availability():
    data = request.get_json()

    slot = data.get("slot")
    enabled = data.get("enabled")

    if not slot:
        return jsonify({"error": "invalid slot"}), 400

    date, slot = slot.split("_")
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    if session[SessionInfo.USER_TYPE] != UserTypes.DOCTOR:
        return jsonify({"error": "invalid user, only doctors can issue this command!"}), 400

    doctor_id = session[SessionInfo.USER_ID]

    with SessionLocal() as db_session:
        availability = db_session.query(DoctorAvailability).filter_by(
            doctor_id=doctor_id,
            date=date,
            slot=slot
        ).first()

        if availability:
            availability.enabled = enabled
        else:
            availability = DoctorAvailability(
                doctor_id=doctor_id,
                date=date,
                slot=slot,
                enabled=enabled
            )
            db_session.add(availability)
        db_session.commit()

    return jsonify({
        "status": "success",
        "slot": slot,
        "enabled": enabled
    })


@api_bp.route("/book_appointment", methods=["POST"])
def book_appointment():
    if session.get(SessionInfo.USER_TYPE) != UserTypes.PATIENT:
        return jsonify({"error": "Only patients can book appointments"}), 403

    patient_id = session.get(SessionInfo.USER_ID)

    data = request.get_json()

    doctor_id = data.get("doctor_id")
    date_str = data.get("date")
    time_str = data.get("time")
    visit_type = data.get("visit_type", "General Consultation")

    if not doctor_id or not date_str or not time_str:
        return jsonify({"error": "doctor_id, date, and time are required"}), 400

    try:
        appointment_date = datetime.date.fromisoformat(date_str)
        appointment_time = datetime.time.fromisoformat(time_str)
    except ValueError:
        return jsonify({"error": "Invalid date/time format"}), 400

    with SessionLocal() as db_session:
        doctor = db_session.get(Doctor, doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        slot = "morning" if appointment_time.hour < 12 else "evening"
        availability = db_session.query(DoctorAvailability).filter_by(
            doctor_id=doctor_id,
            date=appointment_date,
            slot=slot,
            enabled=True
        ).first()

        if not availability:
            return jsonify({"error": f"Doctor unavailable on {date_str} ({slot})"}), 409

        conflict = db_session.query(Appointment).filter_by(
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
            status=AppointmentStatus.BOOKED
        ).first()

        if conflict:
            return jsonify({"error": "This slot is already booked"}), 409

        conflict_self = db_session.query(Appointment).filter_by(
            patient_id=patient_id,
            date=appointment_date,
            time=appointment_time,
            status=AppointmentStatus.BOOKED
        ).first()

        if conflict_self:
            return jsonify({"error": "You already have an appointment booked at this time slot!"}), 409

        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
            visit_type=visit_type,
            status=AppointmentStatus.BOOKED
        )

        db_session.add(new_appointment)
        db_session.commit()

        return jsonify({
            "message": "Appointment booked successfully!",
            "appointment_id": new_appointment.id,
            "doctor_id": doctor_id,
            "date": date_str,
            "time": time_str
        }), 201

@api_bp.route("/doctor/<int:doctor_id>/availability_json")
def availability_json(doctor_id):
    """Return 7-day availability grid for a doctor."""
    from datetime import date, timedelta

    with SessionLocal() as db_session:
        entries = db_session.query(DoctorAvailability).filter_by(
            doctor_id=doctor_id
        ).all()

        avail_map = {
            (a.date, a.slot): a.enabled
            for a in entries
        }

    today = date.today()
    days_out = 7
    schedule = []

    for i in range(days_out):
        d = today + timedelta(days=i)

        morning = avail_map.get((d, "morning"), False)
        evening = avail_map.get((d, "evening"), False)

        schedule.append({
            "doctor_id": doctor_id,
            "date": d.isoformat(),
            "date_display": d.strftime("%d/%m/%Y"),
            "morning": {
                "label": "08:00 - 12:00 am",
                "available": morning
            },
            "evening": {
                "label": "04:00 - 09:00 pm",
                "available": evening
            }
        })

    return jsonify(schedule)


@api_bp.route("/appointments/upcoming", methods=["GET"])
def get_upcoming_appointments():
    with (SessionLocal() as db_session):
        upcoming = db_session.query(Appointment).filter(Appointment.status != AppointmentStatus.COMPLETED).all()
        data = [
            {
                "id": app.id,
                "patient_name": app.patient.name,
                "doctor_name": app.doctor.name,
                "doctor_dep": app.doctor.department.name,
                "patient_id": app.patient.id,
                "date": app.date.isoformat(),
                "time": app.time.isoformat(),
                "status": app.status.value,
            }
            for app in upcoming
        ]
        return jsonify(data)


@api_bp.route("/appointments/past", methods=["GET"])
def get_past_appointments():
    with SessionLocal() as db_session:
        completed = db_session.query(Appointment).filter(Appointment.status == AppointmentStatus.COMPLETED).all()
        data = [
            {
                "id": app.id,
                "patient_name": app.patient.name,
                "doctor_name": app.doctor.name,
                "doctor_dep": app.doctor.department.name,
                "patient_id": app.patient.id,
                "date": app.date.isoformat(),
                "time": app.time.isoformat(),
                "status": app.status.value,
            }
            for app in completed
        ]
        return jsonify(data)
