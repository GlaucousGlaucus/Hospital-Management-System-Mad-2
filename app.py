import os
from typing import Any, Optional

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from models.main_models import Admin, Base, Department, Doctor, Patient
from logging import getLogger

from utils.constants import DB_PATH

logger = getLogger(__name__)

app = Flask(__name__)
app.secret_key = "SECRET"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Session factory
SessionLocal = scoped_session(sessionmaker(bind=engine))

if DB_PATH.exists():
    logger.info(f"DB already exists at {DB_PATH}")
else:
    Base.metadata.create_all(engine)
    admin = Admin(name="Admin", email="admin@nodomain.com", password="")
    with SessionLocal() as session:
        session.add_all([Department(name=f"D{i}", description=f"Description {i}") for i in range(10)])
        session.add(admin)
        session.commit()
    logger.info(f"DB created at {DB_PATH}")

@app.teardown_appcontext
def shutdown_session(exception=None):
    """
    Ensure the session is closed after each request.
    We don't want to leave any sessions open otherwise bad things can happen.
    """
    SessionLocal.remove()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# TODO: Improve UI for login and signup pages
@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/signup', methods=['GET', 'POST'])
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

            if not new_user:
                flash("Please select a valid account type!", "error")
                return redirect(url_for("signup"))
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
    with SessionLocal() as db_session:
        deps = db_session.query(Department).all()
    return render_template('signup.html', departments=deps)
