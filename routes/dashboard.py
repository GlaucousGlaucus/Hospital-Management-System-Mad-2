from logging import getLogger

from flask import Blueprint, render_template, session, redirect, url_for

from models.main_models import SessionLocal, Doctor, Patient, Appointment
from utils.constants import SessionInfo, UserTypes, Routes

logger = getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

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
