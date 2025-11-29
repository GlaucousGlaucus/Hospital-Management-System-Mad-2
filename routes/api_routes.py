import datetime
from logging import getLogger
from typing import List

from flask import (
    Blueprint, jsonify, abort, render_template,
    flash, redirect, url_for, request, session
)
from sqlalchemy.orm import joinedload

from models.main_models import (
    Doctor, Patient, SessionLocal, Appointment,
    DoctorAvailability, AppointmentStatus,
    Department, AvailabilitySlot
)
from utils.constants import SessionInfo, UserTypes, Routes

logger = getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

def require_role(*roles):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            user_type = session.get(SessionInfo.USER_TYPE)
            if user_type not in roles:
                return jsonify({"error": "forbidden"}), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

def require_login(fn):
    def wrapper(*args, **kwargs):
        if not session.get(SessionInfo.USER_ID):
            return jsonify({"error": "login required"}), 401
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

def ensure_doctor_owns(appt):
    return appt.doctor_id == session.get(SessionInfo.USER_ID)

def ensure_patient_owns(appt):
    return appt.patient_id == session.get(SessionInfo.USER_ID)

@api_bp.route("/<entity>/all", methods=["GET"])
@require_role(UserTypes.ADMIN)
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
                    {
                        "id": d.id,
                        "name": d.name,
                        "age": d.age,
                        "email": d.email,
                        "contact": d.contact,
                        "specialization": d.specialization or "",
                        "is_blacklisted": d.is_blacklisted,
                    }
                    for d in entities
                ]
            case "patients":
                data = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "age": p.age,
                        "email": p.email,
                        "contact": p.contact,
                        "is_blacklisted": p.is_blacklisted,
                    }
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
@require_role(UserTypes.ADMIN)
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

@api_bp.route("/patient/<int:patient_id>/history")
@require_login
def patient_history(patient_id: int):

    user_type = session.get(SessionInfo.USER_TYPE)
    user_id = session.get(SessionInfo.USER_ID)

    if user_type == UserTypes.PATIENT and user_id != patient_id:
        return abort(403)

    with SessionLocal() as db:
        patient = (
            db.query(Patient)
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

        doctor = patient.appointments[0].doctor if patient.appointments else None
        department = doctor.department if doctor and doctor.department else None

        visits = []
        for idx, appt in enumerate(patient.appointments, start=1):
            t = appt.treatment
            visits.append({
                "no": idx,
                "visit_type": appt.visit_type or "N/A",
                "tests_done": appt.test_done or "N/A",
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

@api_bp.route("/doctor/appointment/<int:appointment_id>/complete", methods=["POST"])
@require_role(UserTypes.ADMIN, UserTypes.DOCTOR)
def mark_complete(appointment_id):
    with SessionLocal() as db:
        appt = db.get(Appointment, appointment_id)
        if not appt:
            return abort(404)

        user_type = session.get(SessionInfo.USER_TYPE)

        if user_type == UserTypes.DOCTOR and not ensure_doctor_owns(appt):
            return abort(403)

        appt.status = AppointmentStatus.COMPLETED
        db.commit()

    flash("Appointment marked as complete!", "success")
    return redirect(url_for(Routes.DASHBOARD_ROUTE))

@api_bp.route("/appointment/<int:appointment_id>/cancel", methods=["POST"])
@require_login
def cancel_appointment(appointment_id):
    with SessionLocal() as db:
        appt = db.get(Appointment, appointment_id)
        if not appt:
            return abort(404)

        user_type = session.get(SessionInfo.USER_TYPE)

        if user_type == UserTypes.ADMIN:
            pass
        elif user_type == UserTypes.DOCTOR:
            if not ensure_doctor_owns(appt):
                return abort(403)
        elif user_type == UserTypes.PATIENT:
            if not ensure_patient_owns(appt):
                return abort(403)

        appt.status = AppointmentStatus.CANCELLED
        db.commit()

    flash("Appointment cancelled.", "info")
    return redirect(url_for(Routes.DASHBOARD_ROUTE))

@api_bp.route("/appointment/<int:appointment_id>/reschedule", methods=["POST"])
@require_login
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

    with SessionLocal() as db:
        appt = db.get(Appointment, appointment_id)
        if not appt:
            return abort(404)

        user_type = session.get(SessionInfo.USER_TYPE)

        if user_type == UserTypes.ADMIN:
            pass
        elif user_type == UserTypes.DOCTOR:
            if not ensure_doctor_owns(appt):
                return abort(403)
        elif user_type == UserTypes.PATIENT:
            if not ensure_patient_owns(appt):
                return abort(403)

        conflict = db.query(Appointment).filter_by(
            doctor_id=appt.doctor_id,
            date=new_date,
            time=new_time
        ).first()

        if conflict:
            return jsonify({"error": "Slot already booked"}), 409

        if appt.reschedule_count == 0:
            appt.original_date = appt.date
            appt.original_time = appt.time

        appt.date = new_date
        appt.time = new_time
        appt.reschedule_count += 1
        appt.status = AppointmentStatus.BOOKED

        db.commit()

    return jsonify({"status": "success"})

@api_bp.route("/doctor/update_availability", methods=["POST"])
@require_role(UserTypes.DOCTOR)
def update_availability():
    data = request.get_json()

    slot = data.get("slot")
    enabled = data.get("enabled")

    if not slot:
        return jsonify({"error": "invalid slot"}), 400

    try:
        date_str, slot_str = slot.split("_")
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "Invalid slot format"}), 400

    try:
        slot_enum = AvailabilitySlot(slot_str.lower().capitalize())
    except ValueError:
        return jsonify({"error": f"Invalid slot '{slot_str}'"}), 400

    doctor_id = session.get(SessionInfo.USER_ID)

    with SessionLocal() as db:
        availability = db.query(DoctorAvailability).filter_by(
            doctor_id=doctor_id,
            date=date,
            slot=slot_enum
        ).first()

        if availability:
            availability.enabled = bool(enabled)
        else:
            availability = DoctorAvailability(
                doctor_id=doctor_id,
                date=date,
                slot=slot_enum,
                enabled=bool(enabled)
            )
            db.add(availability)

        db.commit()

    return jsonify({
        "status": "success",
        "date": date.isoformat(),
        "slot": slot_enum.value,
        "enabled": bool(enabled)
    })

@api_bp.route("/book_appointment", methods=["POST"])
@require_role(UserTypes.PATIENT)
def book_appointment():
    patient_id = session.get(SessionInfo.USER_ID)
    data = request.get_json()

    doctor_id = data.get("doctor_id")
    date_str = data.get("date")
    time_str = data.get("time")
    visit_type = data.get("visit_type", "Checkup")

    if not doctor_id or not date_str or not time_str:
        return jsonify({"error": "doctor_id, date, time required"}), 400

    try:
        appt_date = datetime.date.fromisoformat(date_str)
        appt_time = datetime.time.fromisoformat(time_str)
    except ValueError:
        return jsonify({"error": "Invalid date/time"}), 400

    with SessionLocal() as db:
        doctor = db.get(Doctor, doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        hour = appt_time.hour
        if hour < 12:
            slot = AvailabilitySlot.MORNING
        elif hour < 16:
            slot = AvailabilitySlot.AFTERNOON
        else:
            slot = AvailabilitySlot.EVENING

        availability = db.query(DoctorAvailability).filter_by(
            doctor_id=doctor_id,
            date=appt_date,
            slot=slot,
            enabled=True
        ).first()

        if not availability:
            return jsonify({"error": f"Doctor unavailable on {date_str} ({slot})"}), 409

        conflict = db.query(Appointment).filter_by(
            doctor_id=doctor_id,
            date=appt_date,
            time=appt_time,
            status=AppointmentStatus.BOOKED
        ).first()

        if conflict:
            return jsonify({"error": "Slot booked"}), 409

        conflict_self = db.query(Appointment).filter_by(
            patient_id=patient_id,
            date=appt_date,
            time=appt_time,
            status=AppointmentStatus.BOOKED
        ).first()

        if conflict_self:
            return jsonify({"error": "You already have appointment at this time"}), 409

        new_appt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=appt_date,
            time=appt_time,
            visit_type=visit_type,
            status=AppointmentStatus.BOOKED
        )

        db.add(new_appt)
        db.commit()

        return jsonify({
            "message": "Appointment booked successfully!",
            "appointment_id": new_appt.id,
            "doctor_id": doctor_id,
            "date": date_str,
            "time": time_str
        }), 201

@api_bp.route("/doctor/<int:doctor_id>/availability_json")
@require_login
def availability_json(doctor_id):
    from datetime import timedelta
    with SessionLocal() as db:
        entries = db.query(DoctorAvailability).filter_by(
            doctor_id=doctor_id
        ).all()

        avail_map = {(a.date, a.slot): a.enabled for a in entries}

    today = datetime.date.today()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    days = [start_of_week + timedelta(days=i) for i in range(7)]
    schedule = []

    for d in days:
        schedule.append({
            "doctor_id": doctor_id,
            "date": d.isoformat(),
            "date_display": d.strftime("%d/%m/%Y"),
            "morning": {
                "label": "08:00 - 12:00 am",
                "available": avail_map.get((d, AvailabilitySlot.MORNING), False)
            },
            "afternoon": {
                "label": "12:00 - 04:00",
                "available": avail_map.get((d, AvailabilitySlot.AFTERNOON), False)
            },
            "evening": {
                "label": "04:00 - 09:00 pm",
                "available": avail_map.get((d, AvailabilitySlot.EVENING), False)
            }
        })

    return jsonify(schedule)

@api_bp.route("/appointments/upcoming", methods=["GET"])
@require_login
def get_upcoming_appointments():
    user_type = session.get(SessionInfo.USER_TYPE)
    user_id = session.get(SessionInfo.USER_ID)

    with SessionLocal() as db:
        query = db.query(Appointment).filter(
            Appointment.status != AppointmentStatus.COMPLETED
        )

        if user_type == UserTypes.DOCTOR:
            query = query.filter(Appointment.doctor_id == user_id)
        elif user_type == UserTypes.PATIENT:
            query = query.filter(Appointment.patient_id == user_id)

        upcoming = query.all()

        data = [
            {
                "id": a.id,
                "patient_name": a.patient.name,
                "doctor_name": a.doctor.name,
                "doctor_dep": a.doctor.department.name,
                "patient_id": a.patient.id,
                "date": a.date.isoformat(),
                "time": a.time.isoformat(),
                "status": a.status.value,
            }
            for a in upcoming
        ]

        return jsonify(data)

@api_bp.route("/appointments/past", methods=["GET"])
@require_login
def get_past_appointments():
    user_type = session.get(SessionInfo.USER_TYPE)
    user_id = session.get(SessionInfo.USER_ID)

    with SessionLocal() as db:
        query = db.query(Appointment).filter(
            Appointment.status == AppointmentStatus.COMPLETED
        )

        if user_type == UserTypes.DOCTOR:
            query = query.filter(Appointment.doctor_id == user_id)
        elif user_type == UserTypes.PATIENT:
            query = query.filter(Appointment.patient_id == user_id)

        completed = query.all()

        data = [
            {
                "id": a.id,
                "patient_name": a.patient.name,
                "doctor_name": a.doctor.name,
                "doctor_dep": a.doctor.department.name,
                "patient_id": a.patient.id,
                "date": a.date.isoformat(),
                "time": a.time.isoformat(),
                "status": a.status.value,
            }
            for a in completed
        ]

        return jsonify(data)

def _admin_search(db, query, today):
    doctors = db.query(Doctor).filter(
        (Doctor.name.ilike(query)) |
        (Doctor.specialization.ilike(query)) |
        (Doctor.email.ilike(query)) |
        (Doctor.contact.ilike(query))
    ).all()

    patients = db.query(Patient).filter(
        (Patient.name.ilike(query)) |
        (Patient.email.ilike(query)) |
        (Patient.contact.ilike(query))
    ).all()

    appointments = (
        db.query(Appointment)
        .join(Appointment.patient)
        .join(Appointment.doctor)
        .join(Doctor.department)
        .filter(
            (Patient.name.ilike(query)) |
            (Doctor.name.ilike(query)) |
            (Department.name.ilike(query))
        ).all()
    )

    return {
        "doctors": [
            {
                "id": d.id,
                "name": d.name,
                "specialization": d.specialization or "",
                "age": d.age,
                "email": d.email,
                "contact": d.contact,
            }
            for d in doctors
        ],
        "patients": [
            {
                "id": p.id,
                "name": p.name,
                "contact": p.contact,
                "email": p.email
            }
            for p in patients
        ],
        "appointments": [
            {
                "id": a.id,
                "patient_name": a.patient.name,
                "patient_id": a.patient.id,
                "doctor_name": a.doctor.name,
                "doctor_dep": a.doctor.department.name,
                "date": a.date.isoformat(),
                "is_upcoming": a.date >= today
            }
            for a in appointments
        ]
    }

def _patient_search(db, query, department=None, date_str=None, slot=None):
    doctors = (
        db.query(Doctor)
        .join(Department)
        .filter(
            (Doctor.name.ilike(query)) |
            (Doctor.specialization.ilike(query)) |
            (Department.name.ilike(query))
        )
        .all()
    )

    if department:
        doctors = [d for d in doctors if str(d.department.id) == department]

    if not date_str or not slot:
        return {
            "doctors": [
                {
                    "id": d.id,
                    "name": d.name,
                    "specialization": d.specialization or "",
                    "age": d.age,
                    "contact": d.contact,
                    "department_id": d.department.id,
                    "department_name": d.department.name
                }
                for d in doctors
            ]
        }

    try:
        selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"doctors": []}

    match slot:
        case "morning":
            slot_enum = AvailabilitySlot.MORNING
        case "afternoon":
            slot_enum = AvailabilitySlot.AFTERNOON
        case "evenening":
            slot_enum = AvailabilitySlot.EVENING
        case "evening":
            slot_enum = AvailabilitySlot.EVENING
        case _:
            return {"doctors": []}

    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.date == selected_date,
        DoctorAvailability.slot == slot_enum,
        DoctorAvailability.enabled == True
    ).all()

    available_ids = {a.doctor_id for a in availability}
    filtered_doctors = [d for d in doctors if d.id in available_ids]

    return {
        "doctors": [
            {
                "id": d.id,
                "name": d.name,
                "specialization": d.specialization or "",
                "age": d.age,
                "contact": d.contact,
                "department_id": d.department.id,
                "department_name": d.department.name
            }
            for d in filtered_doctors
        ]
    }

@api_bp.route("/search", methods=["GET"])
@require_login
def search():
    q = request.args.get("q", "").strip()
    query = f"%{q}%"
    today = datetime.date.today()
    user_type = session.get(SessionInfo.USER_TYPE)

    if not q:
        if user_type == UserTypes.ADMIN:
            return jsonify({"doctors": [], "patients": [], "appointments": []})
        if user_type == UserTypes.PATIENT:
            return jsonify({"doctors": []})
        return jsonify({"error": "invalid user"}), 400

    with SessionLocal() as db:
        if user_type == UserTypes.ADMIN:
            return jsonify(_admin_search(db, query, today))
        elif user_type == UserTypes.PATIENT:
            return jsonify(
                _patient_search(
                    db,
                    query,
                    request.args.get("department"),
                    request.args.get("date"),
                    request.args.get("slot")
                )
            )
        else:
            return jsonify({"error": "forbidden"}), 403

@api_bp.route("/blacklist/<entity>/<int:user_id>", methods=["POST"])
@require_role(UserTypes.ADMIN)
def blacklist_user(entity, user_id):
    model_map = {"doctor": Doctor, "patient": Patient}
    model = model_map.get(entity)

    if not model:
        return jsonify({"error": "Invalid entity"}), 400

    with SessionLocal() as db:
        user = db.get(model, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_blacklisted = True
        db.commit()

    return jsonify({"status": "blacklisted"})

@api_bp.route("/unblacklist/<entity>/<int:user_id>", methods=["POST"])
@require_role(UserTypes.ADMIN)
def unblacklist_user(entity, user_id):
    model_map = {"doctor": Doctor, "patient": Patient}
    model = model_map.get(entity)

    if not model:
        return jsonify({"error": "Invalid entity"}), 400

    with SessionLocal() as db:
        user = db.get(model, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_blacklisted = False
        db.commit()

    return jsonify({"status": "unblacklisted"})
