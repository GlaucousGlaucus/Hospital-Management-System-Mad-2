from logging import getLogger

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from models.main_models import SessionLocal, Doctor, Patient, Appointment, Department, Treatment
from services.doctor_service import create_doctor
from utils.constants import SessionInfo, UserTypes, Routes

logger = getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

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
                        Appointment.status == "BOOKED"
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
                        "date": getattr(a, "date", None),
                        "time": getattr(a, "time", None),
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

            # Pass only plain dicts/lists
            return render_template(
                "dashboard/doctor_dashboard.html",
                doctor=doctor_data,
                appointments=appointment_data,
                patients=patient_data
            )

        case UserTypes.PATIENT:
            return render_template('dashboard/patient_dashboard.html')
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
                age=request.form["age"],
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
            doctor.age = int(request.form["age"])
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
                age=int(request.form["age"]),
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
            patient.age = int(request.form["age"])
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
                joinedload(Appointment.treatment)
            )
            .get(appointment_id)
        )
        if not appointment:
            flash("Appointment not found!", "error")
            return redirect(url_for("dashboard.dashboard"))

        treatment = appointment.treatment or Treatment(appointment_id=appointment.id)

        if request.method == "POST":
            treatment.diagnosis = request.form.get("diagnosis", "")
            treatment.prescription = request.form.get("prescription", "")
            treatment.notes = request.form.get("notes", "")

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
        )
