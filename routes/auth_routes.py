# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

def get_auth_service() -> AuthService:
    return AuthService(current_app.config["DATABASE_PATH"])

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
        err_msg = "ACCESS DENIED — INVALID CREDENTIALS"
        if is_json:
            return jsonify({"error": err_msg, "authenticated": False}), 401
        return render_template("login.html", error=err_msg, next=next_url), 401

    # Authentication succeeded: create secure session
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
