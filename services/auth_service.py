import sqlite3
from typing import Optional, Dict, Any
# pyrefly: ignore [missing-import]
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import get_db_connection

class AuthService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticates an operator using constant-time password hash verification.
        Never reveals whether the username or password was incorrect.
        """
        if not username or not password:
            return None

        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT id, username, password_hash, is_active FROM users WHERE username = ?",
                (username.strip(),)
            )
            user = cursor.fetchone()
            if not user:
                return None

            if not user["is_active"]:
                return None

            if not check_password_hash(user["password_hash"], password):
                return None

            return {
                "id": user["id"],
                "username": user["username"]
            }
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves user profile information without exposing the password hash."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT id, username, created_at, is_active FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            if not user:
                return None
            return {
                "id": user["id"],
                "username": user["username"],
                "created_at": user["created_at"],
                "is_active": bool(user["is_active"])
            }
        finally:
            conn.close()

    def create_user(self, username: str, password: str, is_active: int = 1) -> Dict[str, Any]:
        """Creates a new operator with a securely hashed password."""
        if not username or not password:
            raise ValueError("Username and password are required.")

        conn = get_db_connection(self.db_path)
        try:
            pw_hash = generate_password_hash(password)
            with conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash, is_active) VALUES (?, ?, ?)",
                    (username.strip(), pw_hash, is_active)
                )
                user_id = cursor.lastrowid
            return {
                "id": user_id,
                "username": username.strip(),
                "is_active": bool(is_active)
            }
        finally:
            conn.close()
