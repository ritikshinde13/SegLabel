import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from database.db import get_db_connection
from models.workload import IdentityStatus
from models.communication import CommunicationRequest, AuditLog
from services.identity_manager import IdentityManager
from services.policy_engine import PolicyEngine

class CommunicationEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.identity_mgr = IdentityManager(db_path)
        self.policy_engine = PolicyEngine(db_path)

    def simulate_request(
        self,
        workload_id: str,
        destination: str,
        override_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulates a communication attempt from workload_id to destination.
        Enforces Fail-Closed Zero Trust if workload identity is STARTING or AMBIGUOUS.
        """
        workload = self.identity_mgr.get_workload(workload_id)
        if not workload:
            raise ValueError(f"Workload '{workload_id}' not found.")

        now_iso = override_timestamp or datetime.now(timezone.utc).isoformat()
        req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

        current_status = workload.status
        identity_at_decision = workload.current_identity

        # Determine if we are within the ambiguity window
        # An ambiguity window is defined from workload.started_at until confirmed_at (or ongoing if unconfirmed).
        in_ambiguity_window = False
        if current_status in (IdentityStatus.STARTING.value, IdentityStatus.AMBIGUOUS.value):
            in_ambiguity_window = True
        elif workload.confirmed_at and now_iso < workload.confirmed_at:
            in_ambiguity_window = True

        # CORE SECURITY DECISION
        if in_ambiguity_window:
            decision = "DENY"
            reason = "IDENTITY_AMBIGUOUS"
            explanation = (
                f"Workload identity '{identity_at_decision}' is unconfirmed (Status: {current_status}). "
                f"Zero Trust Fail-Closed Rule enforced: communication MUST be denied by default during ambiguity window."
            )
            applicable_policy = "DENY_BY_DEFAULT_AMBIGUITY"
        else:
            # Identity is CONFIRMED - apply normal segmentation policy
            decision, reason, explanation = self.policy_engine.evaluate(
                source_identity=identity_at_decision,
                destination=destination
            )
            applicable_policy = f"{identity_at_decision} -> {destination} ({decision})"

        # Persist request and audit log
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO communication_requests (
                        id, workload_id, source_identity, destination, identity_status,
                        decision, reason, in_ambiguity_window, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        req_id,
                        workload_id,
                        identity_at_decision,
                        destination,
                        current_status,
                        decision,
                        reason,
                        1 if in_ambiguity_window else 0,
                        now_iso
                    )
                )

                conn.execute(
                    """
                    INSERT INTO audit_logs (
                        request_id, workload_id, source, destination, identity_at_decision,
                        identity_status, decision, reason, timestamp, in_ambiguity_window
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        req_id,
                        workload_id,
                        workload_id,
                        destination,
                        identity_at_decision,
                        current_status,
                        decision,
                        reason,
                        now_iso,
                        1 if in_ambiguity_window else 0
                    )
                )
        finally:
            conn.close()

        return {
            "request_id": req_id,
            "workload_id": workload_id,
            "source": workload_id,
            "destination": destination,
            "current_identity": identity_at_decision,
            "current_identity_state": current_status,
            "identity_status": current_status,
            "applicable_policy": applicable_policy,
            "decision": decision,
            "reason": reason,
            "explanation": explanation,
            "in_ambiguity_window": in_ambiguity_window,
            "timestamp": now_iso
        }

    def inject_tampered_request(
        self,
        workload_id: str,
        destination: str,
        decision: str = "ALLOW",
        reason: str = "TAMPERED_BYPASS",
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Injects a tampered/unsafe communication request inside an ambiguity window.
        Specifically used to test and demonstrate that Retroactive Verification
        detects security breaches and flags FAIL.
        """
        workload = self.identity_mgr.get_workload(workload_id)
        if not workload:
            raise ValueError(f"Workload '{workload_id}' not found.")

        req_id = f"REQ-BREACH-{uuid.uuid4().hex[:6].upper()}"
        ts = timestamp or datetime.now(timezone.utc).isoformat()

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO communication_requests (
                        id, workload_id, source_identity, destination, identity_status,
                        decision, reason, in_ambiguity_window, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        req_id,
                        workload_id,
                        workload.initial_identity_signal,
                        destination,
                        IdentityStatus.AMBIGUOUS.value,
                        decision,
                        reason,
                        1,
                        ts
                    )
                )
                conn.execute(
                    """
                    INSERT INTO audit_logs (
                        request_id, workload_id, source, destination, identity_at_decision,
                        identity_status, decision, reason, timestamp, in_ambiguity_window
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        req_id,
                        workload_id,
                        workload_id,
                        destination,
                        workload.initial_identity_signal,
                        IdentityStatus.AMBIGUOUS.value,
                        decision,
                        reason,
                        ts,
                        1
                    )
                )
        finally:
            conn.close()

        return {
            "request_id": req_id,
            "workload_id": workload_id,
            "destination": destination,
            "decision": decision,
            "reason": reason,
            "in_ambiguity_window": True,
            "timestamp": ts
        }
