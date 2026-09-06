from datetime import datetime, timezone
import time
from typing import Dict, Any, List
from database.db import get_db_connection, reset_db
from models.workload import IdentityStatus
from services.identity_manager import IdentityManager
from services.communication_engine import CommunicationEngine
from services.verification_service import VerificationService

class DemoService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.identity_mgr = IdentityManager(db_path)
        self.comm_engine = CommunicationEngine(db_path)
        self.verification_svc = VerificationService(db_path)

    def run_security_demo(self) -> Dict[str, Any]:
        """
        Executes the official 8-step microsegmentation ambiguity window security demo.
        Guarantees idempotency and records trace output for each phase.
        """
        steps_trace: List[Dict[str, Any]] = []

        # Ensure clean state for the demo workloads
        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute("DELETE FROM verification_results WHERE workload_id IN ('W-OLD', 'W-NEW')")
            conn.execute("DELETE FROM audit_logs WHERE workload_id IN ('W-OLD', 'W-NEW')")
            conn.execute("DELETE FROM communication_requests WHERE workload_id IN ('W-OLD', 'W-NEW')")
            conn.execute("DELETE FROM identity_events WHERE workload_id IN ('W-OLD', 'W-NEW')")
            conn.execute("DELETE FROM workloads WHERE id IN ('W-OLD', 'W-NEW')")
        conn.close()

        # Step 1: Create old workload W-OLD with identity 'payment', status CONFIRMED
        w_old = self.identity_mgr.create_workload(
            workload_id="W-OLD",
            name="Legacy Payment Gateway",
            initial_identity_signal="payment",
            status=IdentityStatus.CONFIRMED.value,
            confirmed_identity="payment"
        )
        steps_trace.append({
            "step": 1,
            "title": "Create Established Workload (W-OLD)",
            "workload_id": "W-OLD",
            "identity": "payment",
            "status": w_old.status,
            "description": "Established workload W-OLD registered with confirmed identity 'payment'.",
            "status_badge": "CONFIRMED",
            "timestamp": w_old.started_at
        })

        # Small delay to ensure timestamp separation
        time.sleep(0.01)

        # Step 2: Create new workload W-NEW with reused identity signal 'payment'
        w_new = self.identity_mgr.create_workload(
            workload_id="W-NEW",
            name="New Ingestion Worker",
            initial_identity_signal="payment"
        )
        assert w_new.status == IdentityStatus.AMBIGUOUS.value, f"Expected AMBIGUOUS, got {w_new.status}"
        steps_trace.append({
            "step": 2,
            "title": "Detect Identity Reuse Collision (W-NEW)",
            "workload_id": "W-NEW",
            "initial_signal": "payment",
            "status": w_new.status,
            "warning": "⚠ Identity ambiguity detected! Reason: Identity signal reused by another workload (W-OLD)",
            "description": "W-NEW attempted to report signal 'payment' which was previously claimed by W-OLD. System flagged workload as AMBIGUOUS.",
            "status_badge": "AMBIGUOUS",
            "timestamp": w_new.started_at
        })

        # Step 3: Attempt W-NEW -> database
        req_step3 = self.comm_engine.simulate_request("W-NEW", "database")
        assert req_step3["decision"] == "DENY", f"Expected DENY, got {req_step3['decision']}"
        assert req_step3["reason"] == "IDENTITY_AMBIGUOUS", f"Expected IDENTITY_AMBIGUOUS, got {req_step3['reason']}"
        steps_trace.append({
            "step": 3,
            "title": "Communication Attempt: W-NEW -> database",
            "source": "W-NEW",
            "destination": "database",
            "identity_state": req_step3["current_identity_state"],
            "decision": req_step3["decision"],
            "reason": req_step3["reason"],
            "in_ambiguity_window": True,
            "description": "Request to database denied because W-NEW identity is AMBIGUOUS. Fail-closed default applied.",
            "status_badge": "DENIED",
            "timestamp": req_step3["timestamp"]
        })

        # Step 4: Attempt W-NEW -> payment-api
        req_step4 = self.comm_engine.simulate_request("W-NEW", "payment-api")
        assert req_step4["decision"] == "DENY", f"Expected DENY, got {req_step4['decision']}"
        assert req_step4["reason"] == "IDENTITY_AMBIGUOUS", f"Expected IDENTITY_AMBIGUOUS, got {req_step4['reason']}"
        steps_trace.append({
            "step": 4,
            "title": "Communication Attempt: W-NEW -> payment-api",
            "source": "W-NEW",
            "destination": "payment-api",
            "identity_state": req_step4["current_identity_state"],
            "decision": req_step4["decision"],
            "reason": req_step4["reason"],
            "in_ambiguity_window": True,
            "description": "CRITICAL SECURITY CHECK: Even though 'payment' normally has ALLOW permission to payment-api, communication was DENIED because identity has not been confirmed!",
            "status_badge": "DENIED",
            "timestamp": req_step4["timestamp"]
        })

        time.sleep(0.01)

        # Step 5: Confirm W-NEW -> student
        w_new_confirmed = self.identity_mgr.confirm_identity("W-NEW", "student")
        assert w_new_confirmed.status == IdentityStatus.CONFIRMED.value
        assert w_new_confirmed.confirmed_identity == "student"
        steps_trace.append({
            "step": 5,
            "title": "Identity Attestation: Confirm W-NEW as 'student'",
            "workload_id": "W-NEW",
            "previous_signal": "payment",
            "confirmed_identity": "student",
            "status": w_new_confirmed.status,
            "ambiguity_window_closed_at": w_new_confirmed.confirmed_at,
            "description": "Attestation completed. W-NEW's true identity is 'student'. Ambiguity window is now closed. Normal segmentation policies will apply.",
            "status_badge": "CONFIRMED",
            "timestamp": w_new_confirmed.confirmed_at
        })

        # Step 6: Try W-NEW -> database
        req_step6 = self.comm_engine.simulate_request("W-NEW", "database")
        assert req_step6["decision"] == "DENY", f"Expected DENY, got {req_step6['decision']}"
        assert req_step6["reason"] == "POLICY_DENY", f"Expected POLICY_DENY, got {req_step6['reason']}"
        steps_trace.append({
            "step": 6,
            "title": "Post-Confirmation Attempt: W-NEW -> database",
            "source": "W-NEW",
            "destination": "database",
            "evaluated_identity": "student",
            "decision": req_step6["decision"],
            "reason": req_step6["reason"],
            "in_ambiguity_window": False,
            "description": "Request evaluated against confirmed 'student' identity. Rule 'student -> database = DENY' enforced.",
            "status_badge": "DENIED",
            "timestamp": req_step6["timestamp"]
        })

        # Step 7: Try W-NEW -> student-api
        req_step7 = self.comm_engine.simulate_request("W-NEW", "student-api")
        assert req_step7["decision"] == "ALLOW", f"Expected ALLOW, got {req_step7['decision']}"
        assert req_step7["reason"] == "POLICY_ALLOW", f"Expected POLICY_ALLOW, got {req_step7['reason']}"
        steps_trace.append({
            "step": 7,
            "title": "Post-Confirmation Attempt: W-NEW -> student-api",
            "source": "W-NEW",
            "destination": "student-api",
            "evaluated_identity": "student",
            "decision": req_step7["decision"],
            "reason": req_step7["reason"],
            "in_ambiguity_window": False,
            "description": "Request evaluated against confirmed 'student' identity. Rule 'student -> student-api = ALLOW' permitted.",
            "status_badge": "ALLOWED",
            "timestamp": req_step7["timestamp"]
        })

        # Step 8: Run retroactive verification
        verification = self.verification_svc.verify_ambiguity_window("W-NEW")
        assert verification["result"] == "PASS", f"Expected PASS, got {verification['result']}"
        assert verification["allowed_in_window"] == 0
        assert verification["wrong_identity_access"] == 0
        assert verification["total_attempts"] >= 2

        steps_trace.append({
            "step": 8,
            "title": "Retroactive Security Verification",
            "workload_id": "W-NEW",
            "ambiguity_window": f"{verification['window_start']} -> {verification['window_end']}",
            "communication_attempts": verification["total_attempts"],
            "allowed_during_window": verification["allowed_in_window"],
            "denied_during_window": verification["denied_in_window"],
            "wrong_identity_access": verification["wrong_identity_access"],
            "result": verification["result"],
            "verdict_text": verification["verdict_text"],
            "summary": verification["summary"],
            "status_badge": "PASS",
            "description": "VERIFICATION RESULT: PASS ✓ — Ambiguity window successfully inspected. Zero communications were permitted based on unconfirmed or ambiguous identity.",
            "timestamp": verification["verified_at"]
        })

        return {
            "success": True,
            "demo_name": "Workload Identity Ambiguity Window in Microsegmentation",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "steps": steps_trace,
            "final_verification": verification
        }

    def run_scenario_reconnaissance_burst(self) -> Dict[str, Any]:
        """Scenario: Attacker launches aggressive port-scan probe burst during startup -> triggers automated quarantine."""
        from services.spiffe_service import SpiffeService
        steps: List[Dict[str, Any]] = []

        # Cleanup test workload
        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute("DELETE FROM verification_results WHERE workload_id = 'W-RECON-ATTACKER'")
            conn.execute("DELETE FROM audit_logs WHERE workload_id = 'W-RECON-ATTACKER'")
            conn.execute("DELETE FROM communication_requests WHERE workload_id = 'W-RECON-ATTACKER'")
            conn.execute("DELETE FROM identity_events WHERE workload_id = 'W-RECON-ATTACKER'")
            conn.execute("DELETE FROM workloads WHERE id = 'W-RECON-ATTACKER'")
        conn.close()

        # Step 1: Rogue container boots claiming admin identity
        w = self.identity_mgr.create_workload(
            workload_id="W-RECON-ATTACKER",
            name="Rogue Ingress Container",
            initial_identity_signal="admin",
            status=IdentityStatus.STARTING.value
        )
        steps.append({
            "step": 1,
            "title": "Rogue Container Starts",
            "description": "Container started claiming 'admin' identity. Status: STARTING (Fail-Closed).",
            "status_badge": "STARTING",
            "workload_id": "W-RECON-ATTACKER"
        })

        # Step 2: Fires 5 rapid probe requests to diverse internal endpoints
        probed = ["database", "payment-api", "student-api", "admin-api", "analytics-service"]
        for idx, dest in enumerate(probed, start=1):
            res = self.comm_engine.simulate_request("W-RECON-ATTACKER", dest)
            steps.append({
                "step": 1 + idx,
                "title": f"Probe Attempt #{idx}: Egress to {dest}",
                "description": f"Attempt to connect to {dest}. Blocked by Zero Trust rule: {res['reason']}.",
                "decision": res["decision"],
                "reason": res["reason"],
                "status_badge": "DENIED"
            })

        # Step 3: 6th request triggers automated hostile reconnaissance threshold and QUARANTINE
        burst_req = self.comm_engine.simulate_request("W-RECON-ATTACKER", "database")
        w_after = self.identity_mgr.get_workload("W-RECON-ATTACKER")
        steps.append({
            "step": 7,
            "title": "Rate Limit Threshold Exceeded -> Automated Quarantine",
            "description": f"Excessive probe attempts detected. Workload automatically isolated into {w_after.status}. Reason: {burst_req['reason']}.",
            "decision": burst_req["decision"],
            "reason": burst_req["reason"],
            "status_badge": "QUARANTINED"
        })

        return {
            "success": True,
            "scenario_id": "reconnaissance_burst",
            "title": "Hostile Ambiguity Reconnaissance & Automated Containment",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "steps": steps
        }

    def run_scenario_spiffe_forgery(self) -> Dict[str, Any]:
        """Scenario: Attacker presents a cryptographically forged SPIFFE JWT SVID token."""
        from services.spiffe_service import SpiffeService
        spiffe = SpiffeService()
        steps: List[Dict[str, Any]] = []

        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute("DELETE FROM workloads WHERE id = 'W-SVID-FORGER'")
            conn.execute("DELETE FROM identity_events WHERE workload_id = 'W-SVID-FORGER'")
            conn.execute("DELETE FROM communication_requests WHERE workload_id = 'W-SVID-FORGER'")
            conn.execute("DELETE FROM audit_logs WHERE workload_id = 'W-SVID-FORGER'")
        conn.close()

        # Step 1: Workload starts
        w = self.identity_mgr.create_workload("W-SVID-FORGER", "Cryptographic Probe Pod", "untrusted-worker")
        steps.append({
            "step": 1,
            "title": "Workload Bootstrapping",
            "description": "Workload started with unconfirmed signal 'untrusted-worker'. Status: STARTING.",
            "status_badge": "STARTING"
        })

        # Step 2: Attacker generates a legitimate SVID for 'student'
        legit_svid = spiffe.issue_svid("W-SVID-FORGER", "student")
        steps.append({
            "step": 2,
            "title": "SPIFFE SVID Minted",
            "description": f"SPIRE issued legitimate SVID: {legit_svid['spiffe_id']} signed by HMAC-SHA256.",
            "status_badge": "SVID_ISSUED",
            "token_preview": legit_svid["token"][:35] + "..."
        })

        # Step 3: Attacker tampers with token payload to claim 'admin'
        tampered_token = legit_svid["token"][:-6] + "BADSIG"
        is_valid, claims, err = spiffe.verify_svid(tampered_token)
        steps.append({
            "step": 3,
            "title": "Cryptographic Verification of Forged SVID",
            "description": f"Attacker presented forged/tampered SVID token. Verification verdict: {err}.",
            "status_badge": "FORGERY_BLOCKED",
            "error": err
        })

        # Step 4: Verification of original untampered token passes
        is_valid_real, claims_real, _ = spiffe.verify_svid(legit_svid["token"])
        assert is_valid_real is True
        self.identity_mgr.confirm_identity("W-SVID-FORGER", claims_real["identity"])
        steps.append({
            "step": 4,
            "title": "Valid SVID Attestation Succeeds",
            "description": f"Authentic cryptographic token accepted. Workload safely attested as '{claims_real['identity']}'. Ambiguity window closed.",
            "status_badge": "CONFIRMED"
        })

        return {
            "success": True,
            "scenario_id": "spiffe_forgery",
            "title": "Cryptographic SPIFFE SVID Token Tampering & Verification",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "steps": steps
        }

    def run_scenario_runtime_drift(self) -> Dict[str, Any]:
        """Scenario: Workload is confirmed, but runtime scanner detects container exploit -> identity is REVOKED."""
        steps: List[Dict[str, Any]] = []

        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute("DELETE FROM workloads WHERE id = 'W-DRIFT-TARGET'")
            conn.execute("DELETE FROM identity_events WHERE workload_id = 'W-DRIFT-TARGET'")
            conn.execute("DELETE FROM communication_requests WHERE workload_id = 'W-DRIFT-TARGET'")
            conn.execute("DELETE FROM audit_logs WHERE workload_id = 'W-DRIFT-TARGET'")
        conn.close()

        # Step 1: Create confirmed payment workload
        w = self.identity_mgr.create_workload(
            "W-DRIFT-TARGET", "Critical Payment Pod", "payment",
            status=IdentityStatus.CONFIRMED.value, confirmed_identity="payment"
        )
        steps.append({
            "step": 1,
            "title": "Normal Operation: Workload Confirmed",
            "description": "Payment worker operational with confirmed identity 'payment'.",
            "status_badge": "CONFIRMED"
        })

        # Step 2: Normal allowed request
        req1 = self.comm_engine.simulate_request("W-DRIFT-TARGET", "payment-api")
        assert req1["decision"] == "ALLOW"
        steps.append({
            "step": 2,
            "title": "Valid Request: W-DRIFT-TARGET -> payment-api",
            "description": f"Legitimate traffic allowed: {req1['applicable_policy']}.",
            "decision": req1["decision"],
            "reason": req1["reason"],
            "status_badge": "ALLOWED"
        })

        # Step 3: Runtime anomaly detected (Falco rule: shell spawned in container) -> Revocation triggered
        self.identity_mgr.revoke_workload(
            "W-DRIFT-TARGET",
            reason="Runtime Anomaly: CVE-2026-RCE exploit detected by kernel security probe."
        )
        w_revoked = self.identity_mgr.get_workload("W-DRIFT-TARGET")
        steps.append({
            "step": 3,
            "title": "Runtime Exploit Detected -> Identity Revoked",
            "description": f"Kernel agent flagged container exploit. Workload state transitioned to {w_revoked.status}.",
            "status_badge": "REVOKED"
        })

        # Step 4: Subsequent request fails closed
        req2 = self.comm_engine.simulate_request("W-DRIFT-TARGET", "payment-api")
        assert req2["decision"] == "DENY"
        assert req2["reason"] == "IDENTITY_REVOKED"
        steps.append({
            "step": 4,
            "title": "Post-Revocation Attempt: Immediate Fail-Closed Block",
            "description": f"Attempted egress blocked: {req2['explanation']}",
            "decision": req2["decision"],
            "reason": req2["reason"],
            "status_badge": "DENIED"
        })

        return {
            "success": True,
            "scenario_id": "runtime_drift",
            "title": "Post-Attestation Runtime Drift & Immediate Revocation",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "steps": steps
        }

    def run_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Dispatcher for all attack scenarios."""
        clean_id = scenario_id.lower().strip()
        if clean_id in ("demo", "ip_churn", "1"):
            return self.run_security_demo()
        elif clean_id in ("reconnaissance", "burst", "reconnaissance_burst", "2"):
            return self.run_scenario_reconnaissance_burst()
        elif clean_id in ("spiffe", "forgery", "spiffe_forgery", "3"):
            return self.run_scenario_spiffe_forgery()
        elif clean_id in ("runtime_drift", "revocation", "drift", "4"):
            return self.run_scenario_runtime_drift()
        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")
