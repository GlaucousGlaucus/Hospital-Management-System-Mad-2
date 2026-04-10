from __future__ import annotations

import datetime
from pathlib import Path
from functools import wraps

from flask import Blueprint, jsonify, request, send_file, session
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from models.main_models import (
    Appointment,
    AppointmentStatus,
    AvailabilitySlot,
    Department,
    Doctor,
    DoctorAvailability,
    ExportJob,
    ExportJobStatus,
    Medicine,
    Patient,
    SessionLocal,
    Treatment,
)
from services.doctor_service import create_doctor
from utils.cache import delete_cache_pattern, get_cache, set_cache
from utils.constants import SessionInfo, UserTypes
from utils.helper_functions import update_session_if_self

api_bp = Blueprint("api", __name__, url_prefix="/api")
ENTITY_MODELS = {"doctor": Doctor, "patient": Patient}


def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get(SessionInfo.USER_ID):
            return jsonify({"error": "Login required."}), 401
        return fn(*args, **kwargs)

    return wrapper


def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if session.get(SessionInfo.USER_TYPE) not in roles:
                return jsonify({"error": "Forbidden."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _invalidate_app_cache():
    delete_cache_pattern("app-context:*")
    delete_cache_pattern("dashboard:*")
    delete_cache_pattern("search:*")


def _user_payload():
    user_id = session.get(SessionInfo.USER_ID)
    if not user_id:
        return None
    return {
        "id": user_id,
        "name": session.get(SessionInfo.USER_NAME),
        "email": session.get(SessionInfo.USER_EMAIL),
        "user_type": session.get(SessionInfo.USER_TYPE),
    }


def _serialize_department(dep: Department):
    return {
        "id": dep.id,
        "name": dep.name,
        "description": dep.description,
    }


def _serialize_doctor(doc: Doctor):
    return {
        "id": doc.id,
        "name": doc.name,
        "email": doc.email,
        "contact": doc.contact,
        "age": doc.age,
        "specialization": doc.specialization or "",
        "department_id": doc.department_id,
        "department_name": doc.department.name if doc.department else None,
        "dob": doc.dob.isoformat() if doc.dob else None,
        "is_blacklisted": doc.is_blacklisted,
    }


def _serialize_patient(patient: Patient):
    return {
        "id": patient.id,
        "name": patient.name,
        "email": patient.email,
        "contact": patient.contact,
        "age": patient.age,
        "dob": patient.dob.isoformat() if patient.dob else None,
        "is_blacklisted": patient.is_blacklisted,
    }


def _apply_user_updates(entity, data: dict):
    entity.name = data.get("name", entity.name).strip()
    entity.email = data.get("email", entity.email).strip()
    entity.contact = data.get("contact", entity.contact).strip()

    if data.get("dob"):
        entity.dob = datetime.date.fromisoformat(data["dob"])
    if data.get("password"):
        entity.password = generate_password_hash(data["password"])


def _serialize_appointment(appt: Appointment):
    return {
        "id": appt.id,
        "date": appt.date.isoformat(),
        "time": appt.time.isoformat(timespec="minutes"),
        "status": appt.status.value,
        "visit_type": appt.visit_type or "",
        "test_done": appt.test_done or "",
        "reschedule_count": appt.reschedule_count,
        "doctor": _serialize_doctor(appt.doctor),
        "patient": _serialize_patient(appt.patient),
    }


def _serialize_schedule_row(day: datetime.date, availability_map: dict[tuple[datetime.date, AvailabilitySlot], bool]):
    return {
        "date": day.isoformat(),
        "date_display": day.strftime("%A, %d %B %Y"),
        "morning": availability_map.get((day, AvailabilitySlot.MORNING), False),
        "afternoon": availability_map.get((day, AvailabilitySlot.AFTERNOON), False),
        "evening": availability_map.get((day, AvailabilitySlot.EVENING), False),
    }


def _schedule_for_doctor(db, doctor_id: int):
    today = datetime.date.today()
    days = [today + datetime.timedelta(days=index) for index in range(7)]
    entries = db.query(DoctorAvailability).filter_by(doctor_id=doctor_id).all()
    availability_map = {(entry.date, entry.slot): entry.enabled for entry in entries}
    return [_serialize_schedule_row(day, availability_map) for day in days]


def _serialize_export_job(export_job: ExportJob):
    return {
        "id": export_job.id,
        "patient_id": export_job.patient_id,
        "patient_name": export_job.patient.name if export_job.patient else None,
        "task_id": export_job.task_id,
        "status": export_job.status.value,
        "file_name": export_job.file_name,
        "error_message": export_job.error_message,
        "created_at": export_job.created_at.isoformat() if export_job.created_at else None,
        "completed_at": export_job.completed_at.isoformat() if export_job.completed_at else None,
        "download_url": (
            f"/api/exports/{export_job.id}/download"
            if export_job.status == ExportJobStatus.COMPLETED and export_job.file_path
            else None
        ),
    }


def _resolve_export_patient(db, patient_id: int | None = None):
    user_id = session.get(SessionInfo.USER_ID)
    user_type = session.get(SessionInfo.USER_TYPE)

    target_patient_id = patient_id or user_id
    patient = db.query(Patient).get(target_patient_id)
    if not patient:
        return None

    if user_type == UserTypes.ADMIN:
        return patient
    if user_type == UserTypes.PATIENT and patient.id == user_id:
        return patient
    if user_type == UserTypes.DOCTOR:
        assigned = db.query(Appointment.id).filter(
            Appointment.doctor_id == user_id,
            Appointment.patient_id == patient.id,
        ).first()
        if assigned:
            return patient
    return None


def _get_export_job_for_current_user(db, export_job_id: int):
    export_job = (
        db.query(ExportJob)
        .options(joinedload(ExportJob.patient))
        .get(export_job_id)
    )
    if not export_job:
        return None

    patient = _resolve_export_patient(db, export_job.patient_id)
    if not patient:
        return None
    return export_job


def _appointment_owner_ok(appt: Appointment):
    user_type = session.get(SessionInfo.USER_TYPE)
    user_id = session.get(SessionInfo.USER_ID)
    if user_type == UserTypes.ADMIN:
        return True
    if user_type == UserTypes.DOCTOR and appt.doctor_id == user_id:
        return True
    if user_type == UserTypes.PATIENT and appt.patient_id == user_id:
        return True
    return False


def _parse_slot(slot: str):
    mapping = {
        "morning": AvailabilitySlot.MORNING,
        "afternoon": AvailabilitySlot.AFTERNOON,
        "evening": AvailabilitySlot.EVENING,
    }
    return mapping.get((slot or "").lower())


def _slot_for_time(appt_time: datetime.time):
    if appt_time.hour < 12:
        return AvailabilitySlot.MORNING
    if appt_time.hour < 16:
        return AvailabilitySlot.AFTERNOON
    return AvailabilitySlot.EVENING


def _slot_time_bounds(slot: AvailabilitySlot):
    if slot == AvailabilitySlot.MORNING:
        return datetime.time(0, 0), datetime.time(12, 0)
    if slot == AvailabilitySlot.AFTERNOON:
        return datetime.time(12, 0), datetime.time(16, 0)
    return datetime.time(16, 0), None


def _build_history_payload(patient: Patient):
    visits = []
    doctor_names = []
    departments = set()

    ordered_appointments = sorted(patient.appointments, key=lambda appt: (appt.date, appt.time))
    for index, appt in enumerate(ordered_appointments, start=1):
        treatment = appt.treatment
        doctor_name = appt.doctor.name if appt.doctor else None
        department_name = appt.doctor.department.name if appt.doctor and appt.doctor.department else None
        if doctor_name:
            doctor_names.append(doctor_name)
        if department_name:
            departments.add(department_name)

        medicines = []
        if treatment:
            for med in treatment.medicines:
                medicines.append({
                    "name": med.name,
                    "morning": med.morning,
                    "afternoon": med.afternoon,
                    "night": med.night,
                    "duration_days": med.duration_days,
                    "instructions": med.instructions,
                })

        visits.append({
            "no": index,
            "appointment_id": appt.id,
            "date": appt.date.isoformat(),
            "time": appt.time.isoformat(timespec="minutes"),
            "status": appt.status.value,
            "visit_type": appt.visit_type or "",
            "tests_done": appt.test_done or "",
            "doctor_name": doctor_name,
            "department_name": department_name,
            "diagnosis": treatment.diagnosis if treatment else "",
            "prescription": treatment.prescription if treatment else "",
            "notes": treatment.notes if treatment else "",
            "medicines": medicines,
        })

    return {
        "patient": _serialize_patient(patient),
        "doctor_names": sorted(set(filter(None, doctor_names))),
        "departments": sorted(departments),
        "visits": visits,
    }


def _admin_search(db, query: str):
    doctors = db.query(Doctor).options(joinedload(Doctor.department)).filter(
        (Doctor.name.ilike(query))
        | (Doctor.specialization.ilike(query))
        | (Doctor.email.ilike(query))
        | (Doctor.contact.ilike(query))
    ).all()

    patients = db.query(Patient).filter(
        (Patient.name.ilike(query))
        | (Patient.email.ilike(query))
        | (Patient.contact.ilike(query))
    ).all()

    appointments = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(Doctor.department),
        )
        .join(Appointment.patient)
        .join(Appointment.doctor)
        .join(Doctor.department)
        .filter(
            (Patient.name.ilike(query))
            | (Doctor.name.ilike(query))
            | (Department.name.ilike(query))
        )
        .all()
    )

    return {
        "doctors": [_serialize_doctor(doc) for doc in doctors],
        "patients": [_serialize_patient(patient) for patient in patients],
        "appointments": [_serialize_appointment(appt) for appt in appointments],
    }


def _patient_search(db, query: str, department: str | None, date_str: str | None, slot: str | None):
    doctors_query = db.query(Doctor).options(joinedload(Doctor.department))
    if query:
        pattern = f"%{query}%"
        doctors_query = doctors_query.join(Department).filter(
            (Doctor.name.ilike(pattern))
            | (Doctor.specialization.ilike(pattern))
            | (Department.name.ilike(pattern))
        )

    doctors = doctors_query.all()

    if department:
        doctors = [doctor for doctor in doctors if str(doctor.department_id) == str(department)]

    if date_str and slot:
        try:
            selected_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return {"doctors": []}

        slot_enum = _parse_slot(slot)
        if not slot_enum:
            return {"doctors": []}

        availability = db.query(DoctorAvailability).filter(
            DoctorAvailability.date == selected_date,
            DoctorAvailability.slot == slot_enum,
            DoctorAvailability.enabled.is_(True),
        ).all()
        available_ids = {entry.doctor_id for entry in availability}
        doctors = [doctor for doctor in doctors if doctor.id in available_ids]

    return {"doctors": [_serialize_doctor(doctor) for doctor in doctors]}


@api_bp.route("/app-context", methods=["GET"])
def app_context():
    user = _user_payload()
    cache_key = f"app-context:{user['user_type']}:{user['id']}" if user else "app-context:anonymous"
    cached = get_cache(cache_key)
    if cached is not None:
        return jsonify(cached)

    with SessionLocal() as db:
        departments = db.query(Department).order_by(Department.name).all()
        payload = {
            "user": user,
            "departments": [_serialize_department(dep) for dep in departments],
        }
    set_cache(cache_key, payload, ttl_seconds=120)
    return jsonify(payload)


@api_bp.route("/dashboard", methods=["GET"])
@require_login
def dashboard_data():
    user = _user_payload()
    cache_key = f"dashboard:{user['user_type']}:{user['id']}"
    cached = get_cache(cache_key)
    if cached is not None:
        return jsonify(cached)

    with SessionLocal() as db:
        user_id = user["id"]
        user_type = user["user_type"]

        if user_type == UserTypes.ADMIN:
            doctors = db.query(Doctor).options(joinedload(Doctor.department)).order_by(Doctor.name).all()
            patients = db.query(Patient).order_by(Patient.name).all()
            total_appointments = db.query(Appointment).count()
            upcoming = (
                db.query(Appointment)
                .options(
                    joinedload(Appointment.patient),
                    joinedload(Appointment.doctor).joinedload(Doctor.department),
                )
                .filter(Appointment.status == AppointmentStatus.BOOKED)
                .order_by(Appointment.date, Appointment.time)
                .all()
            )
            past = (
                db.query(Appointment)
                .options(
                    joinedload(Appointment.patient),
                    joinedload(Appointment.doctor).joinedload(Doctor.department),
                )
                .filter(
                    or_(
                        Appointment.status == AppointmentStatus.COMPLETED,
                        Appointment.status == AppointmentStatus.CANCELLED,
                    )
                )
                .order_by(Appointment.date.desc(), Appointment.time.desc())
                .all()
            )
            payload = {
                "role": user_type,
                "doctors": [_serialize_doctor(doc) for doc in doctors],
                "patients": [_serialize_patient(patient) for patient in patients],
                "total_appointments": total_appointments,
                "upcoming_appointments": [_serialize_appointment(appt) for appt in upcoming],
                "past_appointments": [_serialize_appointment(appt) for appt in past],
            }
        elif user_type == UserTypes.DOCTOR:
            doctor = db.query(Doctor).options(joinedload(Doctor.department)).get(user_id)
            upcoming = (
                db.query(Appointment)
                .options(
                    joinedload(Appointment.patient),
                    joinedload(Appointment.doctor).joinedload(Doctor.department),
                )
                .filter(
                    Appointment.doctor_id == user_id,
                    Appointment.status == AppointmentStatus.BOOKED,
                )
                .order_by(Appointment.date, Appointment.time)
                .all()
            )
            completed = (
                db.query(Appointment)
                .options(joinedload(Appointment.patient))
                .filter(
                    Appointment.doctor_id == user_id,
                    Appointment.status == AppointmentStatus.COMPLETED,
                )
                .all()
            )
            patients = (
                db.query(Patient)
                .join(Appointment)
                .filter(Appointment.doctor_id == user_id)
                .distinct()
                .order_by(Patient.name)
                .all()
            )
            payload = {
                "role": user_type,
                "doctor": _serialize_doctor(doctor),
                "upcoming_appointments": [_serialize_appointment(appt) for appt in upcoming],
                "completed_appointments": [_serialize_appointment(appt) for appt in completed],
                "patients": [_serialize_patient(patient) for patient in patients],
                "availability": _schedule_for_doctor(db, user_id),
            }
        else:
            patient = db.query(Patient).get(user_id)
            upcoming = (
                db.query(Appointment)
                .options(
                    joinedload(Appointment.patient),
                    joinedload(Appointment.doctor).joinedload(Doctor.department),
                )
                .filter(
                    Appointment.patient_id == user_id,
                    Appointment.status == AppointmentStatus.BOOKED,
                )
                .order_by(Appointment.date, Appointment.time)
                .all()
            )
            export_jobs = (
                db.query(ExportJob)
                .filter(ExportJob.patient_id == user_id)
                .order_by(ExportJob.created_at.desc())
                .limit(5)
                .all()
            )
            payload = {
                "role": user_type,
                "patient": _serialize_patient(patient),
                "departments": [_serialize_department(dep) for dep in db.query(Department).order_by(Department.name).all()],
                "upcoming_appointments": [_serialize_appointment(appt) for appt in upcoming],
                "export_jobs": [_serialize_export_job(job) for job in export_jobs],
            }

    set_cache(cache_key, payload, ttl_seconds=120)
    return jsonify(payload)


@api_bp.route("/departments/<int:department_id>", methods=["GET"])
@require_login
def department_details(department_id: int):
    with SessionLocal() as db:
        department = db.query(Department).options(joinedload(Department.doctors)).get(department_id)
        if not department:
            return jsonify({"error": "Department not found."}), 404
        doctors = (
            db.query(Doctor)
            .options(joinedload(Doctor.department))
            .filter(Doctor.department_id == department_id)
            .order_by(Doctor.name)
            .all()
        )
        return jsonify({
            "department": _serialize_department(department),
            "doctors": [_serialize_doctor(doc) for doc in doctors],
        })


@api_bp.route("/patients/<int:patient_id>/history", methods=["GET"])
@require_login
def patient_history(patient_id: int):
    if session.get(SessionInfo.USER_TYPE) == UserTypes.PATIENT and session.get(SessionInfo.USER_ID) != patient_id:
        return jsonify({"error": "Forbidden."}), 403

    with SessionLocal() as db:
        patient = (
            db.query(Patient)
            .options(
                joinedload(Patient.appointments)
                .joinedload(Appointment.treatment)
                .joinedload(Treatment.medicines),
                joinedload(Patient.appointments)
                .joinedload(Appointment.doctor)
                .joinedload(Doctor.department),
            )
            .filter(Patient.id == patient_id)
            .first()
        )
        if not patient:
            return jsonify({"error": "Patient not found."}), 404
        return jsonify(_build_history_payload(patient))


@api_bp.route("/appointments/<int:appointment_id>/history", methods=["GET"])
@require_role(UserTypes.ADMIN, UserTypes.DOCTOR)
def appointment_history_editor(appointment_id: int):
    with SessionLocal() as db:
        appt = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor).joinedload(Doctor.department),
                joinedload(Appointment.treatment).joinedload(Treatment.medicines),
            )
            .get(appointment_id)
        )
        if not appt:
            return jsonify({"error": "Appointment not found."}), 404
        if not _appointment_owner_ok(appt):
            return jsonify({"error": "Forbidden."}), 403

        treatment = appt.treatment
        return jsonify({
            "appointment": _serialize_appointment(appt),
            "treatment": {
                "diagnosis": treatment.diagnosis if treatment else "",
                "prescription": treatment.prescription if treatment else "",
                "notes": treatment.notes if treatment else "",
                "medicines": [
                    {
                        "name": med.name,
                        "morning": med.morning,
                        "afternoon": med.afternoon,
                        "night": med.night,
                        "duration_days": med.duration_days,
                        "instructions": med.instructions,
                    }
                    for med in (treatment.medicines if treatment else [])
                ],
            },
        })


@api_bp.route("/appointments/<int:appointment_id>/history", methods=["PUT"])
@require_role(UserTypes.ADMIN, UserTypes.DOCTOR)
def update_appointment_history(appointment_id: int):
    data = request.get_json(silent=True) or {}
    with SessionLocal() as db:
        appt = (
            db.query(Appointment)
            .options(joinedload(Appointment.treatment).joinedload(Treatment.medicines))
            .get(appointment_id)
        )
        if not appt:
            return jsonify({"error": "Appointment not found."}), 404
        if not _appointment_owner_ok(appt):
            return jsonify({"error": "Forbidden."}), 403

        treatment = appt.treatment or Treatment(appointment_id=appt.id)
        appt.visit_type = data.get("visit_type", "").strip()
        appt.test_done = data.get("test_done", "").strip()
        treatment.diagnosis = data.get("diagnosis", "").strip()
        treatment.prescription = data.get("prescription", "").strip()
        treatment.notes = data.get("notes", "").strip()

        for med in list(treatment.medicines):
            db.delete(med)

        for payload in data.get("medicines", []):
            name = (payload.get("name") or "").strip()
            if not name:
                continue
            treatment.medicines.append(Medicine(
                name=name,
                morning=int(payload.get("morning", 0) or 0),
                afternoon=int(payload.get("afternoon", 0) or 0),
                night=int(payload.get("night", 0) or 0),
                duration_days=int(payload.get("duration_days", 1) or 1),
                instructions=(payload.get("instructions") or "").strip() or None,
            ))

        db.add(treatment)
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "Patient history updated successfully."})


@api_bp.route("/profile", methods=["GET"])
@require_login
def get_profile():
    user_type = session.get(SessionInfo.USER_TYPE)
    user_id = session.get(SessionInfo.USER_ID)
    with SessionLocal() as db:
        if user_type == UserTypes.DOCTOR:
            doctor = db.query(Doctor).options(joinedload(Doctor.department)).get(user_id)
            return jsonify({"profile": _serialize_doctor(doctor)})
        if user_type == UserTypes.PATIENT:
            patient = db.query(Patient).get(user_id)
            return jsonify({"profile": _serialize_patient(patient)})
        return jsonify({"profile": _user_payload()})


@api_bp.route("/profile", methods=["PUT"])
@require_login
def update_profile():
    data = request.get_json(silent=True) or {}
    user_type = session.get(SessionInfo.USER_TYPE)
    user_id = session.get(SessionInfo.USER_ID)

    with SessionLocal() as db:
        if user_type == UserTypes.DOCTOR:
            entity = db.query(Doctor).get(user_id)
            entity.specialization = data.get("specialization", entity.specialization)
            if data.get("department_id"):
                entity.department_id = int(data["department_id"])
        elif user_type == UserTypes.PATIENT:
            entity = db.query(Patient).get(user_id)
        else:
            return jsonify({"error": "Profile editing is not supported for admins."}), 400

        _apply_user_updates(entity, data)
        db.commit()
        update_session_if_self(entity, user_type)

    _invalidate_app_cache()
    return jsonify({"message": "Profile updated successfully."})


@api_bp.route("/admin/doctors", methods=["POST"])
@require_role(UserTypes.ADMIN)
def create_doctor_api():
    data = request.get_json(silent=True) or {}
    try:
        with SessionLocal() as db:
            doctor = create_doctor(
                db,
                name=data["name"].strip(),
                email=data["email"].strip(),
                password=data["password"],
                dob=datetime.date.fromisoformat(data["dob"]),
                contact=data["contact"].strip(),
                specialization=data["specialization"].strip(),
                department_id=int(data["department_id"]),
            )
            payload = _serialize_doctor(doctor)
    except KeyError as exc:
        return jsonify({"error": f"Missing field: {exc.args[0]}"}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    _invalidate_app_cache()
    return jsonify({"message": "Doctor created successfully.", "doctor": payload}), 201


@api_bp.route("/admin/doctors/<int:doctor_id>", methods=["GET"])
@require_role(UserTypes.ADMIN)
def get_doctor(doctor_id: int):
    with SessionLocal() as db:
        doctor = db.query(Doctor).options(joinedload(Doctor.department)).get(doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found."}), 404
        return jsonify({"doctor": _serialize_doctor(doctor)})


@api_bp.route("/admin/doctors/<int:doctor_id>", methods=["PUT"])
@require_role(UserTypes.ADMIN)
def update_doctor(doctor_id: int):
    data = request.get_json(silent=True) or {}
    with SessionLocal() as db:
        doctor = db.query(Doctor).get(doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found."}), 404

        _apply_user_updates(doctor, data)
        doctor.specialization = data.get("specialization", doctor.specialization).strip()
        if data.get("department_id"):
            doctor.department_id = int(data["department_id"])
        db.commit()

        payload = _serialize_doctor(doctor)

    _invalidate_app_cache()
    return jsonify({"message": "Doctor updated successfully.", "doctor": payload})


@api_bp.route("/admin/patients", methods=["POST"])
@require_role(UserTypes.ADMIN)
def create_patient():
    data = request.get_json(silent=True) or {}
    required = ["name", "email", "password", "dob", "contact"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing field(s): {', '.join(missing)}"}), 400

    with SessionLocal() as db:
        patient = Patient.create_user(
            db,
            name=data["name"].strip(),
            email=data["email"].strip(),
            password=data["password"],
            dob=datetime.date.fromisoformat(data["dob"]),
            contact=data["contact"].strip(),
            is_blacklisted=False,
        )
        payload = _serialize_patient(patient)

    _invalidate_app_cache()
    return jsonify({"message": "Patient created successfully.", "patient": payload}), 201


@api_bp.route("/admin/patients/<int:patient_id>", methods=["GET"])
@require_role(UserTypes.ADMIN)
def get_patient(patient_id: int):
    with SessionLocal() as db:
        patient = db.query(Patient).get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found."}), 404
        return jsonify({"patient": _serialize_patient(patient)})


@api_bp.route("/admin/patients/<int:patient_id>", methods=["PUT"])
@require_role(UserTypes.ADMIN)
def update_patient(patient_id: int):
    data = request.get_json(silent=True) or {}
    with SessionLocal() as db:
        patient = db.query(Patient).get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found."}), 404

        _apply_user_updates(patient, data)
        db.commit()
        payload = _serialize_patient(patient)

    _invalidate_app_cache()
    return jsonify({"message": "Patient updated successfully.", "patient": payload})


@api_bp.route("/doctor/update_availability", methods=["POST"])
@require_role(UserTypes.DOCTOR, UserTypes.ADMIN)
def update_availability():
    data = request.get_json(silent=True) or {}
    doctor_id = int(data.get("doctor_id") or session.get(SessionInfo.USER_ID))
    slot_identifier = data.get("slot", "")
    enabled = bool(data.get("enabled"))

    if session.get(SessionInfo.USER_TYPE) == UserTypes.DOCTOR and doctor_id != session.get(SessionInfo.USER_ID):
        return jsonify({"error": "Forbidden."}), 403

    try:
        date_str, slot_name = slot_identifier.split("_", 1)
        target_date = datetime.date.fromisoformat(date_str)
        slot_enum = _parse_slot(slot_name)
    except ValueError:
        return jsonify({"error": "Slot format must be YYYY-MM-DD_slotname."}), 400

    if not slot_enum:
        return jsonify({"error": "Invalid slot."}), 400

    with SessionLocal() as db:
        if not enabled:
            slot_start, slot_end = _slot_time_bounds(slot_enum)
            active_appointment_query = db.query(Appointment).filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date == target_date,
                Appointment.status == AppointmentStatus.BOOKED,
                Appointment.time >= slot_start,
            )
            if slot_end is not None:
                active_appointment_query = active_appointment_query.filter(Appointment.time < slot_end)

            active_appointment = active_appointment_query.first()
            if active_appointment:
                return jsonify({
                    "error": "You cannot mark this slot unavailable while you have an active appointment in it."
                }), 409

        availability = db.query(DoctorAvailability).filter_by(
            doctor_id=doctor_id,
            date=target_date,
            slot=slot_enum,
        ).first()
        if availability:
            availability.enabled = enabled
        else:
            db.add(DoctorAvailability(
                doctor_id=doctor_id,
                date=target_date,
                slot=slot_enum,
                enabled=enabled,
            ))
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "Availability updated successfully."})


@api_bp.route("/doctor/<int:doctor_id>/availability_json", methods=["GET"])
@require_login
def availability_json(doctor_id: int):
    with SessionLocal() as db:
        return jsonify(_schedule_for_doctor(db, doctor_id))


@api_bp.route("/appointments/book", methods=["POST"])
@require_role(UserTypes.PATIENT)
def book_appointment():
    data = request.get_json(silent=True) or {}
    patient_id = session.get(SessionInfo.USER_ID)
    doctor_id = data.get("doctor_id")
    date_raw = data.get("date")
    time_raw = data.get("time")

    if not doctor_id or not date_raw or not time_raw:
        return jsonify({"error": "doctor_id, date and time are required."}), 400

    try:
        appt_date = datetime.date.fromisoformat(date_raw)
        appt_time = datetime.time.fromisoformat(time_raw)
    except ValueError:
        return jsonify({"error": "Invalid date or time."}), 400

    slot = _slot_for_time(appt_time)

    with SessionLocal() as db:
        doctor = db.query(Doctor).get(int(doctor_id))
        if not doctor:
            return jsonify({"error": "Doctor not found."}), 404

        availability = db.query(DoctorAvailability).filter_by(
            doctor_id=doctor.id,
            date=appt_date,
            slot=slot,
            enabled=True,
        ).first()
        if not availability:
            return jsonify({"error": "Doctor is unavailable for that slot."}), 409

        doctor_conflict = db.query(Appointment).filter_by(
            doctor_id=doctor.id,
            date=appt_date,
            time=appt_time,
            status=AppointmentStatus.BOOKED,
        ).first()
        patient_conflict = db.query(Appointment).filter_by(
            patient_id=patient_id,
            date=appt_date,
            time=appt_time,
            status=AppointmentStatus.BOOKED,
        ).first()
        if doctor_conflict or patient_conflict:
            return jsonify({"error": "That slot is already booked."}), 409

        appt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor.id,
            date=appt_date,
            time=appt_time,
            visit_type=(data.get("visit_type") or "Checkup").strip(),
            status=AppointmentStatus.BOOKED,
        )
        db.add(appt)
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "Appointment booked successfully."}), 201


@api_bp.route("/appointment/<int:appointment_id>/reschedule", methods=["POST"])
@require_login
def reschedule_appointment(appointment_id: int):
    data = request.get_json(silent=True) or {}
    if not data.get("new_date") or not data.get("new_time"):
        return jsonify({"error": "new_date and new_time are required."}), 400

    try:
        new_date = datetime.date.fromisoformat(data["new_date"])
        new_time = datetime.time.fromisoformat(data["new_time"])
    except ValueError:
        return jsonify({"error": "Invalid date or time."}), 400

    new_slot = _slot_for_time(new_time)

    with SessionLocal() as db:
        appt = db.query(Appointment).get(appointment_id)
        if not appt:
            return jsonify({"error": "Appointment not found."}), 404
        if not _appointment_owner_ok(appt):
            return jsonify({"error": "Forbidden."}), 403

        availability = db.query(DoctorAvailability).filter_by(
            doctor_id=appt.doctor_id,
            date=new_date,
            slot=new_slot,
            enabled=True,
        ).first()
        if not availability:
            return jsonify({"error": "Doctor is unavailable for that slot."}), 409

        doctor_conflict = db.query(Appointment).filter_by(
            doctor_id=appt.doctor_id,
            date=new_date,
            time=new_time,
            status=AppointmentStatus.BOOKED,
        ).first()
        patient_conflict = db.query(Appointment).filter_by(
            patient_id=appt.patient_id,
            date=new_date,
            time=new_time,
            status=AppointmentStatus.BOOKED,
        ).first()
        if (
            (doctor_conflict and doctor_conflict.id != appt.id)
            or (patient_conflict and patient_conflict.id != appt.id)
        ):
            return jsonify({"error": "That slot is already booked."}), 409

        if appt.reschedule_count == 0:
            appt.original_date = appt.date
            appt.original_time = appt.time

        appt.date = new_date
        appt.time = new_time
        appt.reschedule_count += 1
        appt.status = AppointmentStatus.BOOKED
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "Appointment rescheduled successfully."})


@api_bp.route("/appointment/<int:appointment_id>/cancel", methods=["POST"])
@require_login
def cancel_appointment(appointment_id: int):
    with SessionLocal() as db:
        appt = db.query(Appointment).get(appointment_id)
        if not appt:
            return jsonify({"error": "Appointment not found."}), 404
        if not _appointment_owner_ok(appt):
            return jsonify({"error": "Forbidden."}), 403
        appt.status = AppointmentStatus.CANCELLED
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "Appointment cancelled."})


@api_bp.route("/doctor/appointment/<int:appointment_id>/complete", methods=["POST"])
@require_role(UserTypes.ADMIN, UserTypes.DOCTOR)
def mark_complete(appointment_id: int):
    with SessionLocal() as db:
        appt = db.query(Appointment).get(appointment_id)
        if not appt:
            return jsonify({"error": "Appointment not found."}), 404
        if not _appointment_owner_ok(appt):
            return jsonify({"error": "Forbidden."}), 403
        appt.status = AppointmentStatus.COMPLETED
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "Appointment marked as completed."})


@api_bp.route("/search", methods=["GET"])
@require_login
def search():
    q = request.args.get("q", "").strip()
    department = request.args.get("department")
    date_str = request.args.get("date")
    slot = request.args.get("slot")
    user_type = session.get(SessionInfo.USER_TYPE)

    cache_key = f"search:{user_type}:{q}:{department}:{date_str}:{slot}"
    cached = get_cache(cache_key)
    if cached is not None:
        return jsonify(cached)

    with SessionLocal() as db:
        if user_type == UserTypes.ADMIN:
            if not q:
                payload = {"doctors": [], "patients": [], "appointments": []}
            else:
                payload = _admin_search(db, f"%{q}%")
        elif user_type == UserTypes.PATIENT:
            payload = _patient_search(db, q, department, date_str, slot)
        else:
            return jsonify({"error": "Forbidden."}), 403

    set_cache(cache_key, payload, ttl_seconds=120)
    return jsonify(payload)


@api_bp.route("/blacklist/<entity>/<int:user_id>", methods=["POST"])
@require_role(UserTypes.ADMIN)
def blacklist_user(entity: str, user_id: int):
    model = ENTITY_MODELS.get(entity)
    if not model:
        return jsonify({"error": "Invalid entity."}), 400

    with SessionLocal() as db:
        user = db.query(model).get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404
        user.is_blacklisted = True
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "User blacklisted successfully."})


@api_bp.route("/unblacklist/<entity>/<int:user_id>", methods=["POST"])
@require_role(UserTypes.ADMIN)
def unblacklist_user(entity: str, user_id: int):
    model = ENTITY_MODELS.get(entity)
    if not model:
        return jsonify({"error": "Invalid entity."}), 400

    with SessionLocal() as db:
        user = db.query(model).get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404
        user.is_blacklisted = False
        db.commit()

    _invalidate_app_cache()
    return jsonify({"message": "User unblacklisted successfully."})


@api_bp.route("/doctor/<int:item_id>", methods=["DELETE"])
@require_role(UserTypes.ADMIN)
def delete_doctor(item_id: int):
    with SessionLocal() as db:
        doctor = db.query(Doctor).get(item_id)
        if not doctor:
            return jsonify({"error": "Doctor not found."}), 404
        db.delete(doctor)
        db.commit()
    _invalidate_app_cache()
    return jsonify({"message": "Doctor deleted successfully."})


@api_bp.route("/patient/<int:item_id>", methods=["DELETE"])
@require_role(UserTypes.ADMIN)
def delete_patient(item_id: int):
    with SessionLocal() as db:
        patient = db.query(Patient).get(item_id)
        if not patient:
            return jsonify({"error": "Patient not found."}), 404
        db.delete(patient)
        db.commit()
    _invalidate_app_cache()
    return jsonify({"message": "Patient deleted successfully."})


@api_bp.route("/exports", methods=["GET"])
@api_bp.route("/patient/exports", methods=["GET"])
@require_login
def list_exports():
    patient_id = request.args.get("patient_id", type=int)
    with SessionLocal() as db:
        patient = _resolve_export_patient(db, patient_id)
        if not patient:
            return jsonify({"error": "Patient not found or access denied."}), 404

        exports = (
            db.query(ExportJob)
            .options(joinedload(ExportJob.patient))
            .filter(ExportJob.patient_id == patient.id)
            .order_by(ExportJob.created_at.desc())
            .all()
        )
        return jsonify({
            "patient": _serialize_patient(patient),
            "exports": [_serialize_export_job(export_job) for export_job in exports],
        })


@api_bp.route("/exports/treatments", methods=["POST"])
@api_bp.route("/patient/exports/treatments", methods=["POST"])
@require_login
def queue_treatment_export():
    from tasks import generate_patient_treatment_csv_export

    data = request.get_json(silent=True) or {}
    requested_patient_id = data.get("patient_id")
    try:
        target_patient_id = int(requested_patient_id) if requested_patient_id else None
    except (TypeError, ValueError):
        return jsonify({"error": "patient_id must be an integer."}), 400

    with SessionLocal() as db:
        patient = _resolve_export_patient(db, target_patient_id)
        if not patient:
            return jsonify({"error": "Patient not found or access denied."}), 404

        export_job = ExportJob(
            patient_id=patient.id,
            status=ExportJobStatus.QUEUED,
        )
        db.add(export_job)
        db.commit()
        db.refresh(export_job)
        task = generate_patient_treatment_csv_export.delay(export_job.id)
        export_job.task_id = task.id
        db.commit()
        payload = _serialize_export_job(export_job)

    _invalidate_app_cache()
    return jsonify({"message": "Treatment export queued.", "export": payload}), 202


@api_bp.route("/exports/<int:export_job_id>", methods=["GET"])
@api_bp.route("/patient/exports/<int:export_job_id>", methods=["GET"])
@require_login
def get_export(export_job_id: int):
    with SessionLocal() as db:
        export_job = _get_export_job_for_current_user(db, export_job_id)
        if not export_job:
            return jsonify({"error": "Export job not found."}), 404
        return jsonify({"export": _serialize_export_job(export_job)})


@api_bp.route("/exports/<int:export_job_id>/download", methods=["GET"])
@api_bp.route("/patient/exports/<int:export_job_id>/download", methods=["GET"])
@require_login
def download_export(export_job_id: int):
    with SessionLocal() as db:
        export_job = _get_export_job_for_current_user(db, export_job_id)
        if not export_job:
            return jsonify({"error": "Export job not found."}), 404
        if export_job.status != ExportJobStatus.COMPLETED or not export_job.file_path:
            return jsonify({"error": "Export file is not ready yet."}), 409
        file_path = Path(export_job.file_path)

    if not file_path.exists():
        return jsonify({"error": "Export file is missing."}), 404
    return send_file(file_path, as_attachment=True, download_name=export_job.file_name or file_path.name)


@api_bp.route("/batch/reports/daily-summary", methods=["POST"])
@require_role(UserTypes.ADMIN)
def queue_daily_summary():
    from tasks import generate_daily_summary_report

    task = generate_daily_summary_report.delay()
    return jsonify({"task_id": task.id, "status": "queued"}), 202


@api_bp.route("/batch/reports/daily-reminders", methods=["POST"])
@require_role(UserTypes.ADMIN)
def queue_daily_reminders():
    from tasks import send_daily_patient_reminders

    task = send_daily_patient_reminders.delay()
    return jsonify({"task_id": task.id, "status": "queued"}), 202


@api_bp.route("/batch/reports/monthly-activity", methods=["POST"])
@require_role(UserTypes.ADMIN)
def queue_monthly_activity_report():
    from tasks import send_monthly_doctor_activity_reports

    task = send_monthly_doctor_activity_reports.delay()
    return jsonify({"task_id": task.id, "status": "queued"}), 202


@api_bp.route("/batch/tasks/<task_id>", methods=["GET"])
@require_role(UserTypes.ADMIN)
def task_status(task_id: str):
    from celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    payload = {"task_id": task_id, "state": result.state}
    if result.successful():
        payload["result"] = result.result
    elif result.failed():
        payload["error"] = str(result.result)
    return jsonify(payload)
