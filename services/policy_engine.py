import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from database.db import get_db_connection
from models.policy import Policy, Destination, PolicyAction

class PolicyEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_destinations(self) -> List[Destination]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM destinations ORDER BY name ASC").fetchall()
            return [Destination(name=r["name"], description=r["description"], category=r["category"]) for r in rows]
        finally:
            conn.close()

    def add_destination(self, name: str, description: Optional[str] = None, category: str = "service") -> Destination:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO destinations (name, description, category) VALUES (?, ?, ?)",
                    (name, description, category)
                )
            return Destination(name=name, description=description, category=category)
        finally:
            conn.close()

    def destination_exists(self, destination: str) -> bool:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute("SELECT 1 FROM destinations WHERE name = ?", (destination,)).fetchone()
            return row is not None
        finally:
            conn.close()

    def is_known_identity(self, identity: str) -> bool:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute("SELECT 1 FROM policies WHERE source_identity = ? LIMIT 1", (identity,)).fetchone()
            return row is not None
        finally:
            conn.close()

    def list_policies(self) -> List[Policy]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM policies ORDER BY source_identity ASC, destination ASC").fetchall()
            return [
                Policy(
                    id=r["id"],
                    source_identity=r["source_identity"],
                    destination=r["destination"],
                    action=r["action"],
                    description=r["description"],
                    created_at=r["created_at"]
                )
                for r in rows
            ]
        finally:
            conn.close()

    def add_policy(self, source_identity: str, destination: str, action: str, description: Optional[str] = None) -> Policy:
        action_clean = action.upper()
        if action_clean not in (PolicyAction.ALLOW.value, PolicyAction.DENY.value):
            raise ValueError(f"Invalid policy action: {action}. Must be ALLOW or DENY.")

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO policies (source_identity, destination, action, description)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(source_identity, destination) DO UPDATE SET
                        action = excluded.action,
                        description = excluded.description
                    """,
                    (source_identity, destination, action_clean, description)
                )
                policy_id = cursor.lastrowid
            return Policy(
                id=policy_id,
                source_identity=source_identity,
                destination=destination,
                action=action_clean,
                description=description
            )
        finally:
            conn.close()

    def delete_policy(self, policy_id: int) -> bool:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute("DELETE FROM policies WHERE id = ?", (policy_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def evaluate(self, source_identity: str, destination: str) -> Tuple[str, str, str]:
        """
        Evaluates normal microsegmentation policy.
        Returns: (decision: ALLOW/DENY, reason: str, explanation: str)
        """
        # 1. Destination validation
        if not self.destination_exists(destination):
            return (
                PolicyAction.DENY.value,
                "INVALID_DESTINATION",
                f"Destination '{destination}' does not exist in the service registry."
            )

        # 2. Identity validation
        if not source_identity or not self.is_known_identity(source_identity):
            return (
                PolicyAction.DENY.value,
                "UNKNOWN_IDENTITY",
                f"Identity '{source_identity}' has no registered policy definitions."
            )

        # 3. Policy rule lookup
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT action, description FROM policies WHERE source_identity = ? AND destination = ?",
                (source_identity, destination)
            ).fetchone()

            if not row:
                return (
                    PolicyAction.DENY.value,
                    "NO_POLICY",
                    f"No matching policy rule for '{source_identity}' -> '{destination}'. Default deny enforced."
                )

            action = row["action"]
            desc = row["description"] or ""
            reason = f"POLICY_{action}"
            explanation = f"Evaluated explicit policy rule: '{source_identity}' -> '{destination}' = {action}. {desc}".strip()
            return (action, reason, explanation)
        finally:
            conn.close()
