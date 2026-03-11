from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")
patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


def _spa_entry():
    return render_template("index.html")


@dashboard_bp.route("/", methods=["GET"])
def dashboard():
    return _spa_entry()


@admin_bp.route("/new/doctor", methods=["GET"])
def new_doctor():
    return _spa_entry()


@admin_bp.route("/edit/doctor/<int:doctor_id>/", methods=["GET"])
def edit_doctor(doctor_id):
    return _spa_entry()


@admin_bp.route("/new/patient", methods=["GET"])
def new_patient():
    return _spa_entry()


@admin_bp.route("/edit/patient/<int:patient_id>", methods=["GET"])
def edit_patient(patient_id):
    return _spa_entry()


@doctor_bp.route("/update_history/<int:appointment_id>", methods=["GET"])
def update_history(appointment_id):
    return _spa_entry()


@doctor_bp.route("/edit", methods=["GET"])
def edit_doctor_self():
    return _spa_entry()


@patient_bp.route("/department/<int:dept_id>", methods=["GET"])
def department_details(dept_id):
    return _spa_entry()


@patient_bp.route("/edit/profile", methods=["GET"])
def edit_patient_profile():
    return _spa_entry()
