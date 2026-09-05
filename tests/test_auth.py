import sqlite3
import pytest
from database.db import get_db_connection

def test_login_page_renders_ok(unauth_client):
    """Verify that the dedicated login page renders with HTTP 200 and required security elements."""
    res = unauth_client.get("/login")
    assert res.status_code == 200
    assert b"Secure Access" in res.data
    assert b"SEG" in res.data
    assert b"Sign In" in res.data
    assert b"username" in res.data.lower()
    assert b"password" in res.data.lower()

def test_valid_login_success_form(unauth_client):
    """Verify that form submission with valid demo credentials authenticates and redirects."""
    res = unauth_client.post("/login", data={
        "username": "admin",
        "password": "SegLabel@2026!",
        "remember_me": "on"
    }, follow_redirects=False)

    assert res.status_code == 302
    assert res.headers["Location"] == "/"

    # Confirm session has been established
    with unauth_client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("username") == "admin"

def test_valid_login_success_json(unauth_client):
    """Verify that AJAX JSON submission returns HTTP 200 with ACCESS GRANTED payload."""
    res = unauth_client.post("/login", json={
        "username": "admin",
        "password": "SegLabel@2026!",
        "remember_me": True
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "ACCESS GRANTED" in data["message"]
    assert data["redirect"] == "/"

    with unauth_client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("username") == "admin"

def test_invalid_credentials_rejected_form(unauth_client):
    """Verify that invalid password produces HTTP 401 and generic error message."""
    res = unauth_client.post("/login", data={
        "username": "admin",
        "password": "WrongPassword123!"
    })

    assert res.status_code == 401
    assert b"ACCESS DENIED" in res.data

    with unauth_client.session_transaction() as sess:
        assert "user_id" not in sess

def test_invalid_credentials_rejected_json(unauth_client):
    """Verify that JSON request with wrong credentials returns HTTP 401."""
    res = unauth_client.post("/login", json={
        "username": "admin",
        "password": "WrongPassword123!"
    })

    assert res.status_code == 401
    data = res.get_json()
    assert "error" in data
    assert "ACCESS DENIED" in data["error"]

def test_nonexistent_user_rejected(unauth_client):
    """Verify that non-existent username returns 401 without revealing username existence."""
    res = unauth_client.post("/login", json={
        "username": "ghost_operator",
        "password": "RandomPassword!"
    })

    assert res.status_code == 401
    data = res.get_json()
    assert "ACCESS DENIED" in data["error"]

def test_empty_credentials_rejected(unauth_client):
    """Verify that empty inputs are rejected with HTTP 400."""
    res = unauth_client.post("/login", json={
        "username": "",
        "password": ""
    })
    assert res.status_code == 400

def test_password_is_hashed_not_plaintext(temp_db):
    """Verify that user passwords are stored exclusively as cryptographic hashes, never plaintext."""
    conn = get_db_connection(temp_db)
    cursor = conn.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    pw_hash = row["password_hash"]
    # Ensure plaintext is never stored
    assert pw_hash != "SegLabel@2026!"
    assert "SegLabel@2026!" not in pw_hash
    # Werkzeug produces scrypt or pbkdf2 format hashes
    assert pw_hash.startswith("scrypt:") or pw_hash.startswith("pbkdf2:")

def test_unauthenticated_ui_redirects_to_login(unauth_client):
    """Verify that unauthenticated GET requests to protected dashboard routes redirect to /login."""
    protected_routes = [
        "/",
        "/workloads",
        "/simulator",
        "/audit",
        "/verification",
        "/policies",
        "/events"
    ]
    for route in protected_routes:
        res = unauth_client.get(route, follow_redirects=False)
        assert res.status_code == 302, f"Route {route} was not redirected"
        assert "/login" in res.headers["Location"]

def test_unauthenticated_api_returns_401(unauth_client):
    """Verify that unauthenticated direct API access is rejected with HTTP 401."""
    res = unauth_client.get("/api/workloads")
    assert res.status_code == 401
    data = res.get_json()
    assert data["authenticated"] is False

def test_authenticated_access_allowed(client):
    """Verify that an authenticated operator session can access dashboard routes and APIs."""
    res = client.get("/")
    assert res.status_code == 200

    api_res = client.get("/api/workloads")
    assert api_res.status_code == 200
    assert isinstance(api_res.get_json(), list)

def test_logout_clears_session(client):
    """Verify that logging out terminates the session and prevents further access."""
    # Ensure logged in
    res = client.get("/")
    assert res.status_code == 200

    # Execute logout
    logout_res = client.post("/logout", follow_redirects=False)
    assert logout_res.status_code == 302
    assert "/login" in logout_res.headers["Location"]

    # Protected dashboard should now redirect to login
    after_res = client.get("/", follow_redirects=False)
    assert after_res.status_code == 302
    assert "/login" in after_res.headers["Location"]

def test_inactive_user_cannot_login(unauth_client, temp_db):
    """Verify that deactivated operators (is_active=0) cannot authenticate."""
    conn = get_db_connection(temp_db)
    conn.execute("UPDATE users SET is_active = 0 WHERE username = 'admin'")
    conn.commit()
    conn.close()

    res = unauth_client.post("/login", json={
        "username": "admin",
        "password": "SegLabel@2026!"
    })
    assert res.status_code == 401

def test_workload_ambiguity_security_preserved(client):
    """
    CRITICAL INVARIANT TEST:
    Verify that the authentication system did not alter or weaken the core workload
    identity ambiguity window security logic:
    - AMBIGUOUS/STARTING workload requests MUST be DENIED.
    - CONFIRMED allowed workload requests MUST be ALLOWED.
    """
    # 1. Create ambiguous workload
    create_res = client.post("/api/workloads", json={
        "id": "W-TEST-AUTH-AMBIG",
        "name": "Auth Ambiguity Workload",
        "initial_identity_signal": "payment",
        "status": "AMBIGUOUS"
    })
    assert create_res.status_code == 201

    # 2. Simulate communication attempt during ambiguity window
    comm_res = client.post("/api/workloads/W-TEST-AUTH-AMBIG/communication", json={
        "destination": "database"
    })
    assert comm_res.status_code == 200
    comm_data = comm_res.get_json()
    assert comm_data["decision"] == "DENY"
    assert comm_data["in_ambiguity_window"] is True
    assert "ambiguous" in comm_data["reason"].lower() or "quarantine" in comm_data["reason"].lower()

    # 3. Confirm workload identity
    confirm_res = client.post("/api/workloads/W-TEST-AUTH-AMBIG/confirm", json={
        "confirmed_identity": "payment"
    })
    assert confirm_res.status_code == 200

    # 4. Post-confirmation communication to allowed destination should succeed
    post_comm = client.post("/api/workloads/W-TEST-AUTH-AMBIG/communication", json={
        "destination": "database"
    })
    assert post_comm.status_code == 200
    post_data = post_comm.get_json()
    assert post_data["decision"] == "ALLOW"

    # 5. Post-confirmation communication to non-allowed destination should be denied by policy
    deny_comm = client.post("/api/workloads/W-TEST-AUTH-AMBIG/communication", json={
        "destination": "student-api"
    })
    assert deny_comm.status_code == 200
    deny_data = deny_comm.get_json()
    assert deny_data["decision"] == "DENY"
