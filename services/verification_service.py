import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from database.db import get_db_connection
from models.communication import VerificationResult
from services.identity_manager import IdentityManager

class VerificationService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.identity_mgr = IdentityManager(db_path)

    def verify_ambiguity_window(self, workload_id: str) -> Dict[str, Any]:
        workload = self.identity_mgr.get_workload(workload_id)
        if not workload:
            raise ValueError(f"Workload '{workload_id}' not found.")

        window_start = workload.started_at
        now_iso = datetime.now(timezone.utc).isoformat()
        window_end = workload.confirmed_at or now_iso
        is_window_closed = workload.confirmed_at is not None

        conn = get_db_connection(self.db_path)
        try:
            # Query all requests recorded during the ambiguity window
            # Either explicit in_ambiguity_window flag or timestamp within window
            query = """
                SELECT * FROM communication_requests
                WHERE workload_id = ?
                  AND (
                      in_ambiguity_window = 1
                      OR (timestamp >= ? AND timestamp <= ?)
                  )
                ORDER BY timestamp ASC
            """
            rows = conn.execute(query, (workload_id, window_start, window_end)).fetchall()

            total_attempts = len(rows)
            allowed_in_window = 0
            denied_in_window = 0
            wrong_identity_access = 0
            flagged_requests: List[Dict[str, Any]] = []

            for r in rows:
                dec = r["decision"].upper()
                if dec == "ALLOW":
                    allowed_in_window += 1
                    # Check if decision was granted under unconfirmed/reused identity
                    if workload.confirmed_identity is None or r["source_identity"] != workload.confirmed_identity:
                        wrong_identity_access += 1
                    flagged_requests.append({
                        "request_id": r["id"],
                        "destination": r["destination"],
                        "identity_used": r["source_identity"],
                        "decision": r["decision"],
                        "reason": r["reason"],
                        "timestamp": r["timestamp"],
                        "violation": "Communication was permitted during unconfirmed ambiguity window"
                    })
                else:
                    denied_in_window += 1

            # Determine security verification result
            if allowed_in_window == 0 and wrong_identity_access == 0:
                result = "PASS"
                verdict_text = "PASS ✓"
                conclusion = "No communication was permitted based on an incorrect or ambiguous identity."
            else:
                result = "FAIL"
                verdict_text = "FAIL ✗"
                conclusion = (
                    f"CRITICAL SECURITY BREACH: {allowed_in_window} communication attempt(s) were ALLOWED "
                    f"during the ambiguity window ({wrong_identity_access} based on unconfirmed/wrong identity)!"
                )

            # Generate ASCII report matching specification
            ascii_report = (
                "====================================\n"
                "RETROACTIVE SECURITY VERIFICATION\n"
                "====================================\n\n"
                f"Workload: {workload.id} ({workload.name})\n"
                f"Ambiguity Window: {window_start} -> {window_end}\n"
                f"Window Status: {'CLOSED (Confirmed)' if is_window_closed else 'OPEN (Pending Confirmation)'}\n"
                f"Confirmed Identity: {workload.confirmed_identity or 'NONE'}\n\n"
                f"Communication Attempts: {total_attempts}\n"
                f"Allowed During Window: {allowed_in_window}\n"
                f"Denied During Window: {denied_in_window}\n\n"
                f"Wrong-Identity Access: {wrong_identity_access}\n\n"
                f"RESULT: {verdict_text}\n\n"
                f"{conclusion}\n"
            )

            if flagged_requests:
                ascii_report += "\nFlagged Violating Requests:\n"
                for req in flagged_requests:
                    ascii_report += (
                        f"  - [{req['request_id']}] -> {req['destination']} "
                        f"(Identity: {req['identity_used']}, Decision: {req['decision']}, Reason: {req['reason']})\n"
                    )

            # Store result in database
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO verification_results (
                        workload_id, window_start, window_end, total_attempts,
                        allowed_in_window, denied_in_window, wrong_identity_access,
                        result, summary, flagged_requests_json, verified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workload_id,
                        window_start,
                        window_end,
                        total_attempts,
                        allowed_in_window,
                        denied_in_window,
                        wrong_identity_access,
                        result,
                        ascii_report,
                        json.dumps(flagged_requests),
                        now_iso
                    )
                )
                res_id = cursor.lastrowid

            return {
                "id": res_id,
                "workload_id": workload_id,
                "workload_name": workload.name,
                "window_start": window_start,
                "window_end": window_end,
                "is_window_closed": is_window_closed,
                "confirmed_identity": workload.confirmed_identity,
                "total_attempts": total_attempts,
                "allowed_in_window": allowed_in_window,
                "denied_in_window": denied_in_window,
                "wrong_identity_access": wrong_identity_access,
                "result": result,
                "verdict_text": verdict_text,
                "summary": ascii_report,
                "flagged_requests": flagged_requests,
                "verified_at": now_iso
            }
        finally:
            conn.close()

    def list_verification_results(self, workload_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            query = """
                SELECT vr.*, w.name as workload_name
                FROM verification_results vr
                JOIN workloads w ON vr.workload_id = w.id
            """
            params = []
            if workload_id:
                query += " WHERE vr.workload_id = ?"
                params.append(workload_id)
            query += " ORDER BY vr.verified_at DESC"

            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                flagged = json.loads(r["flagged_requests_json"]) if r["flagged_requests_json"] else []
                results.append({
                    "id": r["id"],
                    "workload_id": r["workload_id"],
                    "workload_name": r["workload_name"],
                    "window_start": r["window_start"],
                    "window_end": r["window_end"],
                    "total_attempts": r["total_attempts"],
                    "allowed_in_window": r["allowed_in_window"],
                    "denied_in_window": r["denied_in_window"],
                    "wrong_identity_access": r["wrong_identity_access"],
                    "result": r["result"],
                    "summary": r["summary"],
                    "flagged_requests": flagged,
                    "verified_at": r["verified_at"]
                })
            return results
        finally:
            conn.close()
