from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, render_template, request, session

from models.main_models import Admin, Patient, Doctor, SessionLocal
from utils.constants import SessionInfo, UserTypes

auth_signup_bp = Blueprint("auth_signup", __name__, url_prefix="/signup")
auth_login_bp = Blueprint("auth_login", __name__, url_prefix="/login")
auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")

ROLE_MODELS = {
    UserTypes.ADMIN: Admin,
    UserTypes.DOCTOR: Doctor,
    UserTypes.PATIENT: Patient,
}


def _serialize_session_user():
    user_id = session.get(SessionInfo.USER_ID)
    if not user_id:
        return None

    return {
        "id": user_id,
        "name": session.get(SessionInfo.USER_NAME),
        "email": session.get(SessionInfo.USER_EMAIL),
        "user_type": session.get(SessionInfo.USER_TYPE),
    }


def _find_user(db, email: str, user_type: str):
    model = ROLE_MODELS.get(user_type)
    if not model:
        return None
    return db.query(model).filter_by(email=email).first()


def _set_session_for(user, user_type: str):
    session.clear()
    session[SessionInfo.USER_ID] = user.id
    session[SessionInfo.USER_NAME] = user.name
    session[SessionInfo.USER_EMAIL] = user.email
    session[SessionInfo.USER_TYPE] = user_type


@auth_login_bp.route("/", methods=["GET"])
def login():
    return render_template("index.html")


@auth_signup_bp.route("/", methods=["GET"])
def signup():
    return render_template("index.html")


@auth_login_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return render_template("index.html")


@auth_api_bp.route("/session", methods=["GET"])
def current_session():
    return jsonify({"user": _serialize_session_user()})


@auth_api_bp.route("/login", methods=["POST"])
def login_api():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    user_type = data.get("user_type", "")

    if not email or not password or user_type not in (
        UserTypes.ADMIN,
        UserTypes.DOCTOR,
        UserTypes.PATIENT,
    ):
        return jsonify({"error": "Valid email, password and role are required."}), 400

    with SessionLocal() as db:
        user = _find_user(db, email, user_type)
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials."}), 401
        if getattr(user, "is_blacklisted", False):
            return jsonify({"error": "This account has been disabled by the admin."}), 403
        _set_session_for(user, user_type)

    return jsonify({
        "message": "Logged in successfully.",
        "user": _serialize_session_user(),
    })


@auth_api_bp.route("/signup", methods=["POST"])
def signup_api():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    dob_raw = data.get("dob", "")
    contact = data.get("contact", "").strip()

    if not all([name, email, password, dob_raw, contact]):
        return jsonify({"error": "All signup fields are required."}), 400

    try:
        dob = date.fromisoformat(dob_raw)
    except ValueError:
        return jsonify({"error": "Date of birth must be a valid ISO date."}), 400

    with SessionLocal() as db:
        existing = db.query(Patient).filter_by(email=email).first()
        if existing:
            return jsonify({"error": "A patient account already exists for that email."}), 409

        patient = Patient.create_user(
            db,
            name=name,
            email=email,
            password=password,
            dob=dob,
            contact=contact,
            is_blacklisted=False,
        )
        _set_session_for(patient, UserTypes.PATIENT)

    return jsonify({
        "message": "Account created successfully.",
        "user": _serialize_session_user(),
    }), 201


@auth_api_bp.route("/logout", methods=["POST"])
def logout_api():
    session.clear()
    return jsonify({"message": "Logged out successfully."})
