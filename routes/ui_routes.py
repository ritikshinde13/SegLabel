from flask import Blueprint, render_template, current_app
from services.identity_manager import IdentityManager
from services.policy_engine import PolicyEngine
from services.audit_service import AuditService
from services.verification_service import VerificationService

ui_bp = Blueprint("ui", __name__)

def get_services():
    db_path = current_app.config["DATABASE_PATH"]
    return (
        IdentityManager(db_path),
        PolicyEngine(db_path),
        AuditService(db_path),
        VerificationService(db_path)
    )

@ui_bp.route("/")
def index():
    return render_template("index.html")

@ui_bp.route("/workloads")
def workloads_page():
    return render_template("workloads.html")

@ui_bp.route("/simulator")
def simulator_page():
    return render_template("simulator.html")

@ui_bp.route("/audit")
def audit_page():
    return render_template("audit.html")

@ui_bp.route("/verification")
def verification_page():
    return render_template("verification.html")

@ui_bp.route("/policies")
def policies_page():
    return render_template("policies.html")

@ui_bp.route("/events")
def events_page():
    return render_template("events.html")

