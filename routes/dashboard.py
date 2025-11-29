from datetime import datetime, timedelta, date
from logging import getLogger

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from models.main_models import SessionLocal, Doctor, Patient, Appointment, Department, Treatment, DoctorAvailability, Medicine, AppointmentStatus
from services.doctor_service import create_doctor
from utils.constants import SessionInfo, UserTypes, Routes
from utils.helper_functions import update_session_if_self

logger = getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")
patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


def require_login():
    if not session.get(SessionInfo.USER_ID):
        return redirect(url_for(Routes.LOGIN_ROUTE))
    return None


def require_role(role_list):
    user_type = session.get(SessionInfo.USER_TYPE)
    if user_type not in role_list:
        flash("Access denied", "error")
        return redirect(url_for(Routes.DASHBOARD_ROUTE))
    return None


def require_owner_or_admin(entity_doctor_id=None, entity_patient_id=None):
    user_type = session.get(SessionInfo.USER_TYPE)
    user_id = session.get(SessionInfo.USER_ID)
    if user_type == UserTypes.ADMIN:
        return None
    if entity_doctor_id and user_type == UserTypes.DOCTOR and user_id == entity_doctor_id:
        return None
    if entity_patient_id and user_type == UserTypes.PATIENT and user_id == entity_patient_id:
        return None
    flash("Access denied", "error")
    return redirect(url_for(Routes.DASHBOARD_ROUTE))


@patient_bp.route("/department/<int:dept_id>")
def department_details(dept_id):
    r = require_login()
    if r: return r
    with SessionLocal() as s:
        dep = s.query(Department).get(dept_id)
        if not dep:
            flash("Department not found", "error")
            return redirect(url_for(Routes.DASHBOARD_ROUTE))
        doctors = s.query(Doctor).filter(Doctor.department_id == dep.id).all()
    return render_template(
        "patient/department_details.html",
        department={
            "id": dep.id,
            "name": dep.name,
            "description": dep.description
        },
        doctors=[
            {
                "id": d.id,
                "name": d.name,
                "specialization": d.specialization,
                "age": getattr(d, "age", None),
                "contact": getattr(d, "contact", None),
                "qualification": getattr(d, "qualification", None),
                "experience": getattr(d, "experience", None),
                "bio": getattr(d, "bio", None),
            }
            for d in doctors
        ]
    )


@dashboard_bp.route('/')
def dashboard():
    r = require_login()
    if r: return r
    user_type = session.get(SessionInfo.USER_TYPE)
    match user_type:
        case UserTypes.ADMIN:
            return render_template('dashboard/admin_dashboard.html')

        case UserTypes.DOCTOR:
            doctor_id = session.get(SessionInfo.USER_ID)
            with SessionLocal() as db:
                doctor = db.query(Doctor).get(doctor_id)
                if not doctor:
                    flash("Doctor not found", "error")
                    return redirect(url_for(Routes.LOGIN_ROUTE))
                appointments = (
                    db.query(Appointment)
                    .filter(Appointment.doctor_id == doctor_id, Appointment.status == AppointmentStatus.BOOKED)
                    .join(Patient)
                    .add_entity(Patient)
                    .all()
                )
                patients = (
                    db.query(Patient)
                    .join(Appointment)
                    .filter(Appointment.doctor_id == doctor_id)
                    .distinct()
                    .all()
                )
                doctor_data = {
                    "id": doctor.id,
                    "name": doctor.name,
                    "email": doctor.email,
                    "age": doctor.age,
                }
                appointment_data = []
                for a, p in appointments:
                    appointment_data.append({
                        "id": a.id,
                        "status": a.status,
                        "date": a.date,
                        "time": a.time,
                        "patient": {
                            "id": p.id,
                            "name": p.name,
                            "email": p.email,
                            "age": p.age,
                        }
                    })
                patient_data = [
                    {"id": p.id, "name": p.name, "email": p.email, "age": p.age}
                    for p in patients
                ]
                availability = {
                    (d.date, d.slot.value.lower()): d.enabled
                    for d in db.query(DoctorAvailability).filter_by(doctor_id=doctor_id).all()
                }
            today = datetime.today().date()
            start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
            days = [(start_of_week + timedelta(days=i)) for i in range(7)]
            return render_template(
                "dashboard/doctor_dashboard.html",
                doctor=doctor_data,
                appointments=appointment_data,
                patients=patient_data,
                days=days,
                availability=availability,
            )

        case UserTypes.PATIENT:
            patient_id = session.get(SessionInfo.USER_ID)
            with SessionLocal() as db:
                patient = db.query(Patient).get(patient_id)
                if not patient:
                    flash("Patient not found", "error")
                    return redirect(url_for(Routes.LOGIN_ROUTE))
                departments = db.query(Department).all()
                upcoming = (
                    db.query(Appointment)
                    .options(joinedload(Appointment.doctor).joinedload(Doctor.department))
                    .filter(Appointment.patient_id == patient_id, Appointment.status == AppointmentStatus.BOOKED)
                    .order_by(Appointment.date, Appointment.time)
                    .all()
                )
                appointments = []
                for a in upcoming:
                    appointments.append({
                        "id": a.id,
                        "date": a.date,
                        "time_slot": a.time.strftime("%I:%M %p"),
                        "doctor": {
                            "id": a.doctor.id,
                            "name": a.doctor.name,
                            "department": {"name": a.doctor.department.name}
                        }
                    })
                patient_data = {
                    "id": patient.id,
                    "name": patient.name,
                    "email": patient.email,
                    "age": patient.age,
                    "contact": patient.contact,
                }
                dept_data = [{"id": d.id, "name": d.name} for d in departments]
            return render_template(
                "dashboard/patient_dashboard.html",
                patient=patient_data,
                departments=dept_data,
                appointments=appointments,
            )
    return redirect(url_for(Routes.LOGIN_ROUTE))


@admin_bp.route('/new/doctor', methods=['GET', 'POST'])
def new_doctor():
    r = require_login()
    if r: return r
    r = require_role([UserTypes.ADMIN])
    if r: return r
    with SessionLocal() as db:
        if request.method == "POST":
            create_doctor(
                db,
                name=request.form["name"],
                email=request.form["email"],
                password=generate_password_hash(request.form["password"]),
                dob=date.fromisoformat(request.form["dob"]),
                contact=request.form["contact"],
                specialization=request.form["specialization"],
                department_id=int(request.form["department_id"]),
            )
            flash("Doctor added successfully!", "success")
            return redirect(url_for(Routes.DASHBOARD_ROUTE))
        departments = db.query(Department).all()
    return render_template("admin/new_doctor.html", departments=departments)


@admin_bp.route("/edit/doctor/<int:doctor_id>/", methods=["GET", "POST"])
def edit_doctor(doctor_id):
    r = require_login()
    if r: return r
    with SessionLocal() as db:
        doctor = db.query(Doctor).get(doctor_id)
        if not doctor:
            flash("Doctor not found", "error")
            return redirect(url_for(Routes.DASHBOARD_ROUTE))
        oa = require_owner_or_admin(entity_doctor_id=doctor.id)
        if oa: return oa
        if request.method == "POST":
            doctor.name = request.form["name"]
            doctor.email = request.form["email"]
            doctor.dob = date.fromisoformat(request.form["dob"])
            doctor.contact = request.form["contact"]
            doctor.specialization = request.form["specialization"]
            doctor.department_id = int(request.form["department_id"])
            new_password = request.form.get("password", "").strip()
            if new_password:
                doctor.password = generate_password_hash(new_password)
            db.commit()
            update_session_if_self(doctor, UserTypes.DOCTOR)
            flash("Doctor details updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        departments = db.query(Department).all()
    return render_template("admin/new_doctor.html", doctor=doctor, departments=departments)


@admin_bp.route("/new/patient", methods=["GET", "POST"])
def new_patient():
    r = require_login()
    if r: return r
    r = require_role([UserTypes.ADMIN])
    if r: return r
    with SessionLocal() as db:
        if request.method == "POST":
            patient = Patient(
                name=request.form["name"],
                email=request.form["email"],
                password=generate_password_hash(request.form["password"]),
                dob=date.fromisoformat(request.form["dob"]),
                contact=request.form["contact"],
            )
            db.add(patient)
            db.commit()
            flash("Patient account created successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        return render_template("admin/patient_update.html")


@admin_bp.route("edit/patient/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    r = require_login()
    if r: return r
    with SessionLocal() as db:
        patient = db.query(Patient).get(patient_id)
        if not patient:
            flash("Patient not found", "error")
            return redirect(url_for("dashboard.dashboard"))
        oa = require_owner_or_admin(entity_patient_id=patient.id)
        if oa: return oa
        if request.method == "POST":
            patient.name = request.form["name"]
            patient.email = request.form["email"]
            patient.dob = date.fromisoformat(request.form["dob"])
            patient.contact = request.form["contact"]
            new_password = request.form.get("password", "").strip()
            if new_password:
                patient.password = generate_password_hash(new_password)
            db.commit()
            update_session_if_self(patient, UserTypes.PATIENT)
            flash("Patient details updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        return render_template("admin/patient_update.html", patient=patient)


@dashboard_bp.route("doctor/availability")
def availability():
    r = require_login()
    if r: return r
    return render_template("availability_form.html")


@doctor_bp.route("/update_history/<int:appointment_id>", methods=["GET", "POST"])
def update_history(appointment_id):
    r = require_login()
    if r: return r
    r = require_role([UserTypes.DOCTOR, UserTypes.ADMIN])
    if r: return r
    with SessionLocal() as db:
        appt = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor).joinedload(Doctor.department),
                joinedload(Appointment.treatment).joinedload(Treatment.medicines)
            )
            .get(appointment_id)
        )
        if not appt:
            flash("Appointment not found!", "error")
            return redirect(url_for("dashboard.dashboard"))
        if session.get(SessionInfo.USER_TYPE) == UserTypes.DOCTOR and appt.doctor_id != session.get(SessionInfo.USER_ID):
            flash("Access denied", "error")
            return redirect(url_for("dashboard.dashboard"))
        treatment = appt.treatment or Treatment(appointment_id=appt.id)
        medicines = [{
            "name": m.name,
            "m": m.morning,
            "a": m.afternoon,
            "n": m.night,
        } for m in treatment.medicines] if treatment.medicines else []
        if request.method == "POST":
            treatment.diagnosis = request.form.get("diagnosis", "")
            treatment.prescription = request.form.get("prescription", "")
            treatment.notes = request.form.get("notes", "")
            for m in list(treatment.medicines):
                db.delete(m)
            names = request.form.getlist("medicine_name[]")
            m_doses = request.form.getlist("dose_morning[]")
            a_doses = request.form.getlist("dose_afternoon[]")
            n_doses = request.form.getlist("dose_night[]")
            for i in range(len(names)):
                name = names[i].strip()
                if not name:
                    continue
                med = Medicine(
                    name=name,
                    morning=int(m_doses[i]),
                    afternoon=int(a_doses[i]),
                    night=int(n_doses[i]),
                )
                treatment.medicines.append(med)
            db.add(treatment)
            db.commit()
            flash("Patient history updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        patient = appt.patient
        doctor = appt.doctor
        dept = doctor.department.name if doctor.department else "N/A"
        return render_template(
            "doctor/update_patient.html",
            appointment=appt,
            treatment=treatment,
            patient=patient,
            department=dept,
            medicines=medicines
        )


@patient_bp.route("edit/profile", methods=["GET", "POST"])
def edit_patient():
    r = require_login()
    if r: return r
    if session[SessionInfo.USER_TYPE] != UserTypes.PATIENT:
        flash("Access denied", "error")
        return redirect(url_for(Routes.DASHBOARD_ROUTE))
    with SessionLocal() as db:
        patient = db.query(Patient).get(session[SessionInfo.USER_ID])
        if not patient:
            flash("Patient not found", "error")
            return redirect(url_for(Routes.DASHBOARD_ROUTE))
        if request.method == "POST":
            patient.name = request.form["name"]
            patient.email = request.form["email"]
            patient.dob = date.fromisoformat(request.form["dob"])
            patient.contact = request.form["contact"]
            new_password = request.form.get("password", "").strip()
            if new_password:
                patient.password = generate_password_hash(new_password)
            db.commit()
            flash("Patient details updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        return render_template("admin/patient_update.html", patient=patient)


@doctor_bp.route("/edit", methods=["GET", "POST"])
def edit_doctor():
    r = require_login()
    if r: return r
    if session[SessionInfo.USER_TYPE] != UserTypes.DOCTOR:
        flash("Access denied", "error")
        return redirect(url_for(Routes.DASHBOARD_ROUTE))
    return redirect(url_for("admin.edit_doctor", doctor_id=session[SessionInfo.USER_ID]))
