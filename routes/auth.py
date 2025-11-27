from logging import getLogger
from typing import Any, Optional

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.main_models import Admin, Department, Doctor, Patient, SessionLocal
from utils.constants import Routes, UserTypes, SessionInfo

logger = getLogger(__name__)
auth_signup_bp = Blueprint("auth_signup", __name__, url_prefix="/signup")
auth_login_bp = Blueprint("auth_login", __name__, url_prefix="/login")

@auth_login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth_login.login"))

# TODO: Improve UI for login and signup pages
@auth_login_bp.route('/', methods=['GET', 'POST'])
def login():
    match request.method:
        case "POST":
            email: str = request.form["email"]
            password: str = request.form["password"]
            user_type: str = request.form["user_type"]
            user: Optional[Any] = None
            with SessionLocal() as db_session:
                match user_type:
                    case UserTypes.DOCTOR:
                        user = db_session.query(Doctor).filter_by(email=email).first()
                    case UserTypes.PATIENT:
                        user = db_session.query(Patient).filter_by(email=email).first()
                    case UserTypes.ADMIN:
                        user = db_session.query(Admin).filter_by(email=email).first()
                    case _:
                        flash("Invalid user type")
            if user and check_password_hash(user.password, password):
                session[SessionInfo.USER_ID] = user.id
                session[SessionInfo.USER_NAME] = user.name
                session[SessionInfo.USER_EMAIL] = user.email
                session[SessionInfo.USER_TYPE] = user_type
                return redirect(url_for(Routes.DASHBOARD_ROUTE))
            flash("Invalid credentials", "error")
    return render_template('login.html')

@auth_signup_bp.route('/', methods=['GET', 'POST'])
def signup():
    match request.method:
        case "POST":
            role = request.form["role"]
            if role not in ("doctor", "patient"):
                flash("Invalid role", "error")
                return redirect(url_for(Routes.SIGNUP_ROUTE))

            name: str = request.form["name"]
            email: str = request.form["email"]
            password = generate_password_hash(request.form["password"])
            age: int = int(request.form["age"])
            contact: str = request.form["contact"]

            with SessionLocal() as db_session:
                email_exists = db_session.query(Doctor.email).filter_by(email=email).first()
                if email_exists:
                    flash(f"Account with email {email} already exists!", "error")
                    return redirect(url_for(Routes.SIGNUP_ROUTE))

                match role:
                    case "doctor":
                        dep_id: Optional[str] = request.form["department"]
                        if not dep_id.isdigit():
                            flash("Invalid department ID", "error")
                            return redirect(url_for(Routes.SIGNUP_ROUTE))
                        dep_id: int = int(dep_id)
                        dp_exists = db_session.query(Department.id).filter_by(id=dep_id).first()
                        if not dp_exists:
                            flash("This department does not exist", "error")
                            return redirect(url_for(Routes.SIGNUP_ROUTE))

                        Doctor.create_user(
                            db_session,
                            name=name,
                            email=email,
                            password=password,
                            age=age,
                            contact=contact,
                            specialization=request.form["specialization"],
                            department_id=dep_id,
                        )
                        flash("Account created successfully! Please login.", "success")
                        return redirect(url_for(Routes.LOGIN_ROUTE))
                    case "patient":
                        Patient.create_user(
                            db_session,
                            name=name,
                            email=email,
                            password=password,
                            age=age,
                            contact=contact,
                        )
                        flash("Account created successfully! Please login.", "success")
                        return redirect(url_for(Routes.LOGIN_ROUTE))
            flash("Please select a valid account type!", "error")
            return redirect(url_for(Routes.SIGNUP_ROUTE))
    with SessionLocal() as db_session:
        deps = db_session.query(Department).all()
    return render_template('signup.html', departments=deps)

@auth_signup_bp.route('/doctor', methods=['GET', 'POST'])
def signup_doctor():
    if request.method == 'POST':
        dep_id = request.form.get('department')
        if not dep_id or not dep_id.isdigit():
            flash("Invalid department ID", "error")
            return redirect(url_for('signup_doctor'))

        with SessionLocal() as db_session:
            email = request.form['email']
            if db_session.query(Doctor).filter_by(email=email).first():
                flash("Email already exists!", "error")
                return redirect(url_for('signup_doctor'))

            department = db_session.get(Department, int(dep_id))
            if not department:
                flash("Department not found", "error")
                return redirect(url_for('signup_doctor'))

            doctor = Doctor(
                name=request.form['name'],
                email=email,
                specialization=request.form['specialization'],
                department=department,
                password=generate_password_hash(request.form['password'])
            )
            db_session.add(doctor)
            db_session.commit()
            flash("Doctor account created successfully!", "success")
            return redirect(url_for('auth_login.login'))

    deps = SessionLocal().query(Department).all()
    return render_template('signup_doctor.html', departments=deps)
