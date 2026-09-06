import sqlite3
import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

DEFAULT_ADMIN_USERNAME = os.environ.get("SEG_LABEL_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("SEG_LABEL_ADMIN_PASSWORD", "SegLabel@2026!")

DEFAULT_DESTINATIONS = [
    ("database", "Core Relational Database Store", "data"),
    ("payment-api", "Payment Processing Service Endpoint", "service"),
    ("student-api", "Student Records & Course Service Endpoint", "service"),
    ("admin-api", "Privileged Administrative Gateway", "service"),
    ("analytics-service", "Telemetry & Analytics Ingestion", "service"),
]

DEFAULT_POLICIES = [
    ("payment", "database", "ALLOW", "Payment worker full access to database"),
    ("payment", "payment-api", "ALLOW", "Payment worker access to payment processing API"),
    ("student", "database", "DENY", "Student workload strictly forbidden from direct database access"),
    ("student", "student-api", "ALLOW", "Student workload permitted to access student API"),
    ("admin", "database", "ALLOW", "Admin service unrestricted database access"),
    ("admin", "admin-api", "ALLOW", "Admin service access to admin gateway"),
]

def seed_admin_user(conn: sqlite3.Connection, username: str = None, password: str = None) -> None:
    user = username or os.environ.get("SEG_LABEL_ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    pw = password or os.environ.get("SEG_LABEL_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    cursor = conn.execute("SELECT id FROM users WHERE username = ?", (user,))
    if not cursor.fetchone():
        pw_hash = generate_password_hash(pw)
        conn.execute(
            "INSERT INTO users (username, password_hash, is_active) VALUES (?, ?, 1)",
            (user, pw_hash)
        )

def get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str, seed_defaults: bool = True) -> None:
    # Ensure directory exists if it's a file path
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    conn = get_db_connection(db_path)
    with conn:
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='workloads'")
        row = cursor.fetchone()
        if row and row["sql"] and "QUARANTINED" not in row["sql"]:
            conn.execute("PRAGMA foreign_keys = OFF;")
            conn.execute("CREATE TABLE workloads_migration_backup AS SELECT * FROM workloads;")
            conn.execute("DROP TABLE workloads;")
            with open(SCHEMA_FILE, "r") as f:
                conn.executescript(f.read())
            conn.execute("INSERT OR IGNORE INTO workloads SELECT * FROM workloads_migration_backup;")
            conn.execute("DROP TABLE workloads_migration_backup;")
            conn.execute("PRAGMA foreign_keys = ON;")
        else:
            with open(SCHEMA_FILE, "r") as f:
                conn.executescript(f.read())

        if seed_defaults:
            # Seed default admin account
            seed_admin_user(conn)

            # Seed destinations
            for name, desc, cat in DEFAULT_DESTINATIONS:
                conn.execute(
                    "INSERT OR IGNORE INTO destinations (name, description, category) VALUES (?, ?, ?)",
                    (name, desc, cat)
                )

            # Seed policies
            for src, dest, act, desc in DEFAULT_POLICIES:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO policies (source_identity, destination, action, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (src, dest, act, desc)
                )
    conn.close()

def reset_db(db_path: str) -> None:
    """Wipes all dynamic tables and re-seeds default policies, destinations, and admin user."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("DELETE FROM verification_results")
        conn.execute("DELETE FROM audit_logs")
        conn.execute("DELETE FROM communication_requests")
        conn.execute("DELETE FROM identity_events")
        conn.execute("DELETE FROM workloads")
        conn.execute("DELETE FROM policies")
        conn.execute("DELETE FROM destinations")

        seed_admin_user(conn)

        for name, desc, cat in DEFAULT_DESTINATIONS:
            conn.execute(
                "INSERT INTO destinations (name, description, category) VALUES (?, ?, ?)",
                (name, desc, cat)
            )

        for src, dest, act, desc in DEFAULT_POLICIES:
            conn.execute(
                """
                INSERT INTO policies (source_identity, destination, action, description)
                VALUES (?, ?, ?, ?)
                """,
                (src, dest, act, desc)
            )
    conn.close()
