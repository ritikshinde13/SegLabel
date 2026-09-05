import pytest
from models.workload import IdentityStatus

def test_retroactive_verification_passes_when_all_denied(services):
    identity_mgr = services["identity"]
    comm_engine = services["comm"]
    verif_svc = services["verification"]

    # 1. Establish W-OLD
    identity_mgr.create_workload("W-OLD", "Old Worker", "payment", status=IdentityStatus.CONFIRMED.value)

    # 2. Start W-TARGET with reused identity signal
    identity_mgr.create_workload("W-TARGET", "Target Worker", "payment")

    # 3. Simulate requests during ambiguity window
    comm_engine.simulate_request("W-TARGET", "database")
    comm_engine.simulate_request("W-TARGET", "payment-api")
    comm_engine.simulate_request("W-TARGET", "database")

    # 4. Confirm identity
    identity_mgr.confirm_identity("W-TARGET", "student")

    # 5. Run verification
    report = verif_svc.verify_ambiguity_window("W-TARGET")

    assert report["result"] == "PASS"
    assert report["total_attempts"] == 3
    assert report["allowed_in_window"] == 0
    assert report["denied_in_window"] == 3
    assert report["wrong_identity_access"] == 0
    assert "RESULT: PASS ✓" in report["summary"]
    assert "No communication was permitted" in report["summary"]

def test_verification_detects_unsafe_allow_event(services):
    identity_mgr = services["identity"]
    comm_engine = services["comm"]
    verif_svc = services["verification"]

    # Setup workload
    identity_mgr.create_workload("W-OLD2", "Old Worker 2", "payment", status=IdentityStatus.CONFIRMED.value)
    identity_mgr.create_workload("W-BREACH", "Breached Worker", "payment")

    # Legitimate denied request
    comm_engine.simulate_request("W-BREACH", "database")

    # Synthetic / tampered bypass ALLOW request inside ambiguity window
    comm_engine.inject_tampered_request("W-BREACH", "database", decision="ALLOW", reason="FIREWALL_BYPASS_LEAK")

    # Confirm identity
    identity_mgr.confirm_identity("W-BREACH", "student")

    # Run verification
    report = verif_svc.verify_ambiguity_window("W-BREACH")

    assert report["result"] == "FAIL"
    assert report["allowed_in_window"] == 1
    assert report["wrong_identity_access"] == 1
    assert "RESULT: FAIL ✗" in report["summary"]
    assert len(report["flagged_requests"]) == 1
    assert report["flagged_requests"][0]["decision"] == "ALLOW"
    assert report["flagged_requests"][0]["destination"] == "database"
