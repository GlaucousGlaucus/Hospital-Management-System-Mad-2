from logging import getLogger
from typing import Any, Optional

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.main_models import Admin, Department, Doctor, Patient, SessionLocal

logger = getLogger(__name__)
auth_signup_bp = Blueprint("auth_signup", __name__, url_prefix="/signup")
auth_login_bp = Blueprint("auth_login", __name__, url_prefix="/login")

# TODO: Improve UI for login and signup pages
@auth_login_bp.route('/', methods=['GET', 'POST'])
def login():
    match request.method:
        case "POST":
            email: str = request.form["email"]
            password: str = request.form["password"]
            user_type: str = request.form["user_type"]
            user: Optional[Any] = None
            if user_type == "doctor":
                user = Doctor.query.filter_by(email=email).first()
            elif user_type == "patient":
                user = Patient.query.filter_by(email=email).first()
            elif user_type == "admin":
                user = Admin.query.filter_by(email=email).first()
            else:
                flash("Invalid user type")

            if user and check_password_hash(user.password, password):
                session["user_id"] = user.id
                session["role"] = user.role
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "error")
    return render_template('login.html')

@auth_signup_bp.route('/', methods=['GET', 'POST'])
def signup():
    match request.method:
        case "POST":
            role = request.form["role"]
            if role not in ("doctor", "patient"):
                flash("Invalid role", "error")
                return redirect(url_for("signup"))

            hashed_pw = generate_password_hash(request.form["password"])
            new_user = None
            match role:
                case "doctor":
                    dep_id: Optional[str] = request.form["department"]
                    if not dep_id.isdigit():
                        flash("Invalid department ID", "error")
                        return redirect(url_for("signup"))
                    dep_id: int = int(dep_id)
                    new_user = Doctor(
                        name=request.form["name"],
                        email=request.form["email"],
                        specialization=request.form["specialization"],
                        department_id=dep_id,
                        password=hashed_pw,
                    )
                    with SessionLocal() as db_session:
                        email_exists = db_session.query(Doctor.email).filter_by(email=new_user.email).first()
                        dp_exists = db_session.query(Department.id).filter_by(id=new_user.department_id).first()
                        if email_exists:
                            flash(f"Account with email {new_user.email} already exists!", "error")
                            return redirect(url_for("signup"))
                        if not dp_exists:
                            flash("This department does not exist", "error")
                            return redirect(url_for("signup"))
                        db_session.add(new_user)
                        db_session.commit()
                        flash("Account created successfully! Please login.", "success")
                        return redirect(url_for("login"))
            if not new_user:
                flash("Please select a valid account type!", "error")
                return redirect(url_for("signup"))
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
