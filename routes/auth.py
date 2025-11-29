from datetime import date
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
            if user:
                if user.is_blacklisted:
                    flash("Your account has been disabled by admin.", "error")
                    return redirect(url_for("auth_login.login"))

                if check_password_hash(user.password, password):
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
            if role != "patient":
                flash("Invalid role", "error")
                return redirect(url_for(Routes.SIGNUP_ROUTE))

            name: str = request.form["name"]
            email: str = request.form["email"]
            password = generate_password_hash(request.form["password"])
            dob_str = request.form["dob"]
            try:
                dob = date.fromisoformat(dob_str)
            except ValueError:
                flash("Invalid date of birth", "error")
                return redirect(url_for(Routes.SIGNUP_ROUTE))
            contact: str = request.form["contact"]

            with SessionLocal() as db_session:
                email_exists = db_session.query(Patient).filter_by(email=email).first()
                if email_exists:
                    flash(f"Account with email {email} already exists!", "error")
                    return redirect(url_for(Routes.SIGNUP_ROUTE))

                Patient.create_user(
                    db_session,
                    name=name,
                    email=email,
                    password=password,
                    dob=dob,
                    contact=contact,
                )
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for(Routes.LOGIN_ROUTE))
    with SessionLocal() as db_session:
        deps = db_session.query(Department).all()
    return render_template('signup.html', departments=deps)

