from logging import getLogger

from flask import Blueprint, render_template

logger = getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route('/')
def dashboard():
    return render_template('dashboard.html')
