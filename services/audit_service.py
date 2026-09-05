from typing import Optional, List, Dict, Any
from database.db import get_db_connection
from models.communication import AuditLog

class AuditService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_logs(
        self,
        workload_id: Optional[str] = None,
        decision: Optional[str] = None,
        in_ambiguity_window: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []

            if workload_id:
                query += " AND workload_id = ?"
                params.append(workload_id)
            if decision:
                query += " AND decision = ?"
                params.append(decision.upper())
            if in_ambiguity_window is not None:
                query += " AND in_ambiguity_window = ?"
                params.append(1 if in_ambiguity_window else 0)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [
                {
                    "id": r["id"],
                    "request_id": r["request_id"],
                    "workload_id": r["workload_id"],
                    "source": r["source"],
                    "destination": r["destination"],
                    "identity_at_decision": r["identity_at_decision"],
                    "identity_status": r["identity_status"],
                    "decision": r["decision"],
                    "reason": r["reason"],
                    "timestamp": r["timestamp"],
                    "in_ambiguity_window": bool(r["in_ambiguity_window"])
                }
                for r in rows
            ]
        finally:
            conn.close()

    def get_audit_summary(self) -> Dict[str, Any]:
        conn = get_db_connection(self.db_path)
        try:
            total_reqs = conn.execute("SELECT COUNT(*) FROM communication_requests").fetchone()[0]
            allowed_reqs = conn.execute("SELECT COUNT(*) FROM communication_requests WHERE decision = 'ALLOW'").fetchone()[0]
            denied_reqs = conn.execute("SELECT COUNT(*) FROM communication_requests WHERE decision = 'DENY'").fetchone()[0]
            ambiguity_reqs = conn.execute("SELECT COUNT(*) FROM communication_requests WHERE in_ambiguity_window = 1").fetchone()[0]
            ambiguity_allowed = conn.execute("SELECT COUNT(*) FROM communication_requests WHERE in_ambiguity_window = 1 AND decision = 'ALLOW'").fetchone()[0]

            return {
                "total_requests": total_reqs,
                "allowed_requests": allowed_reqs,
                "denied_requests": denied_reqs,
                "ambiguity_window_requests": ambiguity_reqs,
                "ambiguity_window_violations": ambiguity_allowed
            }
        finally:
            conn.close()
