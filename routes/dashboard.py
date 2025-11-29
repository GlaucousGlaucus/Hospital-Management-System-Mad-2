from datetime import datetime, timedelta, date
from logging import getLogger
from typing import List

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from models.main_models import SessionLocal, Doctor, Patient, Appointment, Department, Treatment, DoctorAvailability, \
    Medicine, AppointmentStatus
from services.doctor_service import create_doctor
from utils.constants import SessionInfo, UserTypes, Routes

logger = getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")
patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

@patient_bp.route("/department/<int:dept_id>")
def department_details(dept_id):
    with SessionLocal() as session:
        dep = session.query(Department).get(dept_id)
        doctors = session.query(Doctor).filter(Doctor.department_id == dep.id).all()
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
    user_type = session.get(SessionInfo.USER_TYPE)
    match user_type:
        case UserTypes.ADMIN:
            return render_template(
                'dashboard/admin_dashboard.html'
            )
        case UserTypes.DOCTOR:
            doctor_id = session.get(SessionInfo.USER_ID)
            with SessionLocal() as db_session:
                doctor = db_session.query(Doctor).get(doctor_id)

                appointments = (
                    db_session.query(Appointment)
                    .filter(
                        Appointment.doctor_id == doctor_id,
                        Appointment.status == AppointmentStatus.BOOKED
                    )
                    .join(Patient)
                    .add_entity(Patient)
                    .all()
                )

                patients = (
                    db_session.query(Patient)
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
                    (data.date, data.slot.value.lower()) : data.enabled
                    for data in db_session.query(DoctorAvailability).filter_by(doctor_id=doctor_id).all()
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

            with SessionLocal() as db_session:
                patient = db_session.query(Patient).get(patient_id)
                departments = db_session.query(Department).all()
                upcoming = (
                    db_session.query(Appointment)
                    .options(
                        joinedload(Appointment.doctor).joinedload(Doctor.department)
                    )
                    .filter(
                        Appointment.patient_id == patient_id,
                        Appointment.status == AppointmentStatus.BOOKED
                    )
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
                            "department": {
                                "name": a.doctor.department.name
                            }
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
    with SessionLocal() as db_session:
        if request.method == "POST":
            create_doctor(
                db_session,
                name=request.form["name"],
                email=request.form["email"],
                password=generate_password_hash(request.form["password"]),
                dob = date.fromisoformat(request.form["dob"]),
                contact=request.form["contact"],
                specialization=request.form["specialization"],
                department_id=int(request.form["department_id"]),
            )
            flash("Doctor added successfully!", "success")
            return redirect(url_for(Routes.DASHBOARD_ROUTE))
        departments = db_session.query(Department).all()
    return render_template("admin/new_doctor.html", departments=departments)

@admin_bp.route("/edit/doctor/<int:doctor_id>/", methods=["GET", "POST"])
def edit_doctor(doctor_id):
    with SessionLocal() as db_session:
        doctor = db_session.query(Doctor).get(doctor_id)
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

            db_session.commit()
            flash("Doctor details updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))

        departments = db_session.query(Department).all()
    return render_template("admin/new_doctor.html", doctor=doctor, departments=departments)


@admin_bp.route("/new/patient", methods=["GET", "POST"])
def new_patient():
    with SessionLocal() as db_session:
        if request.method == "POST":
            patient = Patient(
                name=request.form["name"],
                email=request.form["email"],
                password=generate_password_hash(request.form["password"]),
                dob = date.fromisoformat(request.form["dob"]),
                contact=request.form["contact"],
            )
            db_session.add(patient)
            db_session.commit()
            flash("Patient account created successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        return render_template("admin/patient_update.html")


@admin_bp.route("edit/patient/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    with SessionLocal() as db_session:
        patient = db_session.query(Patient).get(patient_id)
        if not patient:
            flash("Patient not found", "error")
            return redirect(url_for("dashboard.dashboard"))

        if request.method == "POST":
            patient.name = request.form["name"]
            patient.email = request.form["email"]
            patient.dob = date.fromisoformat(request.form["dob"])
            patient.contact = request.form["contact"]

            new_password = request.form.get("password", "").strip()
            if new_password:
                patient.password = generate_password_hash(new_password)

            db_session.commit()
            flash("Patient details updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))

        return render_template("admin/patient_update.html", patient=patient)

@dashboard_bp.route("doctor/availability")
def availability():
    return render_template("availability_form.html")

@doctor_bp.route("/update_history/<int:appointment_id>", methods=["GET", "POST"])
def update_history(appointment_id):
    with SessionLocal() as db_session:
        appointment = (
            db_session.query(Appointment)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor).joinedload(Doctor.department),
                joinedload(Appointment.treatment).joinedload(Treatment.medicines)
            )
            .get(appointment_id)
        )
        if not appointment:
            flash("Appointment not found!", "error")
            return redirect(url_for("dashboard.dashboard"))

        treatment = appointment.treatment or Treatment(appointment_id=appointment.id)
        treatment.medicines: List[Medicine]
        medicines = [{
           "name": med.name,
            "m": med.morning,
            "a": med.afternoon,
            "n": med.night,
        } for med in treatment.medicines] if treatment.medicines else []

        if request.method == "POST":
            treatment.diagnosis = request.form.get("diagnosis", "")
            treatment.prescription = request.form.get("prescription", "")
            treatment.notes = request.form.get("notes", "")
            for m in list(treatment.medicines):
                db_session.delete(m)

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

            db_session.add(treatment)
            db_session.commit()
            flash("Patient history updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))

        patient = appointment.patient
        doctor = appointment.doctor
        dept = doctor.department.name if doctor.department else "N/A"

        return render_template(
            "doctor/update_patient.html",
            appointment=appointment,
            treatment=treatment,
            patient=patient,
            department=dept,
            medicines=medicines
        )

@patient_bp.route("edit/profile", methods=["GET", "POST"])
def edit_patient():
    if session[SessionInfo.USER_TYPE] != UserTypes.PATIENT:
        flash("You are not allowed to edit this patient!", "error")
        return redirect(url_for("dashboard.dashboard"))

    with SessionLocal() as db_session:
        patient = db_session.query(Patient).get(session[SessionInfo.USER_ID])
        if not patient:
            flash("Patient not found", "error")
            return redirect(url_for("dashboard.dashboard"))

        if request.method == "POST":
            patient.name = request.form["name"]
            patient.email = request.form["email"]
            patient.dob = date.fromisoformat(request.form["dob"])
            patient.contact = request.form["contact"]

            new_password = request.form.get("password", "").strip()
            if new_password:
                patient.password = generate_password_hash(new_password)

            db_session.commit()
            flash("Patient details updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))

        return render_template("admin/patient_update.html", patient=patient)


@doctor_bp.route("/edit", methods=["GET", "POST"])
def edit_doctor():
    if session[SessionInfo.USER_TYPE] != UserTypes.DOCTOR:
        flash("You are not allowed to edit this doctor!", "error")
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("admin.edit_doctor", doctor_id=session[SessionInfo.USER_ID]))
