import datetime
from logging import getLogger
from typing import List, dataclass_transform

from flask import Blueprint, jsonify, abort, render_template, flash, redirect, url_for, request, session
from sqlalchemy.orm import joinedload

from models.main_models import Doctor, Patient, SessionLocal, Appointment, DoctorAvailability
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
                "visit_type": "In-person",  # could expand later to Online, etc.
                "tests_done": "ECG",  # static for demo; could be dynamic later
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
        appt.status = "COMPLETED"
        db_session.commit()
    flash("Appointment marked as complete!", "success")
    return redirect(url_for("doctor.dashboard"))


@api_bp.route("doctor/appointment/<int:appointment_id>/cancel", methods=["POST"])
def cancel_appointment(appointment_id):
    with SessionLocal() as db_session:
        appt = db_session.query(Appointment).get(appointment_id)
        appt.status = "CANCELED"
        db_session.commit()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("dashboard.dashboard"))

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

