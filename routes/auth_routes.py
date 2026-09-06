# pyrefly: ignore [missing-import]
import time
from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

# In-memory sliding window brute-force mitigation
# Maps IP address -> list of failed attempt timestamps
FAILED_ATTEMPTS = defaultdict(list)
MAX_FAILED_ATTEMPTS = 8
WINDOW_SECONDS = 60

def get_auth_service() -> AuthService:
    return AuthService(current_app.config["DATABASE_PATH"])

def is_rate_limited(ip: str) -> bool:
    """Checks if client IP has exceeded maximum allowed failed attempts in window."""
    if current_app.config.get("TESTING"):
        return False
    now = time.time()
    # Prune expired timestamps
    attempts = [t for t in FAILED_ATTEMPTS[ip] if now - t < WINDOW_SECONDS]
    FAILED_ATTEMPTS[ip] = attempts
    return len(attempts) >= MAX_FAILED_ATTEMPTS

def record_failed_attempt(ip: str):
    """Records a failed authentication timestamp."""
    if not current_app.config.get("TESTING"):
        FAILED_ATTEMPTS[ip].append(time.time())

def clear_attempts(ip: str):
    """Clears failed attempts upon successful authentication."""
    FAILED_ATTEMPTS.pop(ip, None)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If already authenticated, redirect to dashboard or next parameter
    next_url = request.args.get("next") or url_for("ui.index")
    # Sanitize next_url to prevent open redirect
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("ui.index")

    if request.method == "GET":
        if session.get("user_id"):
            return redirect(next_url)
        return render_template("login.html", next=next_url)

    # Handle POST
    is_json = request.is_json
    data = request.get_json(silent=True) if is_json else request.form
    data = data or {}

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()

    # OWASP Brute Force Mitigation (CWE-307)
    if is_rate_limited(client_ip):
        err_msg = "SECURITY LOCKOUT: Too many failed login attempts. Please wait 60 seconds."
        if is_json:
            return jsonify({
                "error": err_msg,
                "authenticated": False,
                "lockout": True
            }), 429
        return render_template("login.html", error=err_msg, next=next_url), 429

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    remember_me = data.get("remember_me") in (True, "true", "1", "on", "yes")

    if not username or not password:
        err_msg = "Please enter both username and password."
        if is_json:
            return jsonify({"error": err_msg, "authenticated": False}), 400
        return render_template("login.html", error=err_msg, next=next_url), 400

    auth_svc = get_auth_service()
    user = auth_svc.authenticate_user(username, password)

    if not user:
        record_failed_attempt(client_ip)
        err_msg = "ACCESS DENIED — INVALID CREDENTIALS"
        if is_json:
            return jsonify({"error": err_msg, "authenticated": False}), 401
        return render_template("login.html", error=err_msg, next=next_url), 401

    # Authentication succeeded: reset lockout counter and create secure session
    clear_attempts(client_ip)
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session.permanent = remember_me

    if is_json:
        return jsonify({
            "status": "success",
            "message": "ACCESS GRANTED",
            "username": user["username"],
            "redirect": next_url
        }), 200

    return redirect(next_url)

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    if request.is_json:
        return jsonify({
            "status": "success",
            "message": "SESSION TERMINATED",
            "redirect": url_for("auth.login")
        }), 200
    return redirect(url_for("auth.login"))
