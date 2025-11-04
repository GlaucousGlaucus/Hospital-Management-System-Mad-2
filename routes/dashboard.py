from logging import getLogger

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash

from models.main_models import SessionLocal, Doctor, Patient, Appointment, Department
from services.doctor_service import create_doctor
from utils.constants import SessionInfo, UserTypes, Routes

logger = getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@dashboard_bp.route('/')
def dashboard():
    user_type = session.get(SessionInfo.USER_TYPE)
    match user_type:
        case UserTypes.ADMIN:
            return render_template(
                'dashboard/admin_dashboard.html'
            )
        case UserTypes.DOCTOR:
            return render_template('dashboard/doctor_dashboard.html')
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
