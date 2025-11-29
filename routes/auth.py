from datetime import date
from logging import getLogger

from flask import (
    Blueprint, flash, redirect, render_template,
    request, session, url_for
)
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

@auth_login_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email: str = request.form.get("email", "").strip()
        password: str = request.form.get("password", "")
        user_type: str = request.form.get("user_type", "")

        if not email or not password or not user_type:
            flash("Please fill all fields", "error")
            return redirect(url_for("auth_login.login"))

        if user_type not in (UserTypes.ADMIN, UserTypes.DOCTOR, UserTypes.PATIENT):
            flash("Invalid user type", "error")
            return redirect(url_for("auth_login.login"))

        with SessionLocal() as db:
            match user_type:
                case UserTypes.DOCTOR:
                    user = db.query(Doctor).filter_by(email=email).first()
                case UserTypes.PATIENT:
                    user = db.query(Patient).filter_by(email=email).first()
                case UserTypes.ADMIN:
                    user = db.query(Admin).filter_by(email=email).first()
                case _:
                    user = None

        if not user:
            flash("Invalid credentials", "error")
            return redirect(url_for("auth_login.login"))

        if hasattr(user, "is_blacklisted") and user.is_blacklisted:
            flash("Your account has been disabled by admin.", "error")
            return redirect(url_for("auth_login.login"))

        if not check_password_hash(user.password, password):
            flash("Invalid credentials", "error")
            return redirect(url_for("auth_login.login"))

        session.clear()
        session[SessionInfo.USER_ID] = user.id
        session[SessionInfo.USER_NAME] = user.name
        session[SessionInfo.USER_EMAIL] = user.email
        session[SessionInfo.USER_TYPE] = user_type

        return redirect(url_for(Routes.DASHBOARD_ROUTE))

    return render_template("login.html")

@auth_signup_bp.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        role = request.form.get("role", "").strip()
        if role != UserTypes.PATIENT:
            flash("Only patients can register.", "error")
            return redirect(url_for("auth_signup.signup"))

        name: str = request.form.get("name", "").strip()
        email: str = request.form.get("email", "").strip()
        raw_password: str = request.form.get("password", "")
        dob_str: str = request.form.get("dob", "")
        contact: str = request.form.get("contact", "").strip()

        if not name or not email or not raw_password or not dob_str or not contact:
            flash("All fields are required.", "error")
            return redirect(url_for("auth_signup.signup"))

        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            flash("Invalid date of birth format.", "error")
            return redirect(url_for("auth_signup.signup"))

        password = generate_password_hash(raw_password)

        with SessionLocal() as db:
            if db.query(Patient).filter_by(email=email).first():
                flash(f"Account with email {email} already exists!", "error")
                return redirect(url_for("auth_signup.signup"))

            Patient.create_user(
                db,
                name=name,
                email=email,
                password=password,
                dob=dob,
                contact=contact,
            )

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for(Routes.LOGIN_ROUTE))

    with SessionLocal() as db:
        deps = db.query(Department).all()

    return render_template("signup.html", departments=deps)
