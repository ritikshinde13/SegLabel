import os
# pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from flask import Flask, request, session, redirect, url_for, jsonify
from config import Config
from database.db import init_db
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from routes.ui_routes import ui_bp

def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database with defaults
    init_db(app.config["DATABASE_PATH"])

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def enforce_authentication():
        # Allow static files and favicon
        if request.path.startswith("/static/") or request.path == "/favicon.ico":
            return None

        # Allow authentication endpoints
        if request.path in ("/login", "/logout"):
            return None

        # Check for active authenticated operator session
        if session.get("user_id"):
            return None

        # Block unauthenticated API access with 401 JSON
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Unauthorized. Please authenticate.",
                "authenticated": False
            }), 401

        # Redirect unauthenticated browser requests to login
        target = request.full_path if request.query_string else request.path
        return redirect(url_for("auth.login", next=target))

    return app

DEFAULT_PORT = 5050

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    print("=" * 60)
    print("SegLabel Unified Microsegmentation Command Center")
    print(f"Single Localhost Server URL: http://localhost:{port}")
    print(f"All features accessible at:  http://localhost:{port}/")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)

