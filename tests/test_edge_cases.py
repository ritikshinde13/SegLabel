import pytest
from models.workload import IdentityStatus

def test_edge_case_1_unknown_identity_denied(services):
    """Edge Case 1: New workload has completely unknown identity."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Workload created with an identity that has no policies defined anywhere
    w = identity_mgr.create_workload("W-UNKNOWN", "Unknown Svc", "mysterious-daemon")
    
    # 1. During startup/ambiguity, communication is DENIED
    res_ambig = comm_engine.simulate_request("W-UNKNOWN", "database")
    assert res_ambig["decision"] == "DENY"
    assert res_ambig["reason"] == "IDENTITY_AMBIGUOUS"

    # 2. Even if confirmed with an unknown identity, policy engine DENIES due to unknown identity
    identity_mgr.confirm_identity("W-UNKNOWN", "mysterious-daemon")
    res_confirmed = comm_engine.simulate_request("W-UNKNOWN", "database")
    assert res_confirmed["decision"] == "DENY"
    assert res_confirmed["reason"] == "UNKNOWN_IDENTITY"

def test_edge_case_2_reused_identity_signal(services):
    """Edge Case 2: Identity signal is reused."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    identity_mgr.create_workload("W-LEGACY", "Legacy Service", "admin", status=IdentityStatus.CONFIRMED.value)
    w_new = identity_mgr.create_workload("W-NEW-ADMIN", "Candidate Admin", "admin")

    assert w_new.status == IdentityStatus.AMBIGUOUS.value
    assert "reused" in w_new.status_reason.lower()

    # Communication must be DENIED even though admin normally has full access
    res = comm_engine.simulate_request("W-NEW-ADMIN", "admin-api")
    assert res["decision"] == "DENY"
    assert res["reason"] == "IDENTITY_AMBIGUOUS"

def test_edge_case_3_identity_becomes_confirmed(services):
    """Edge Case 3: Identity becomes confirmed -> normal policy applies."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    identity_mgr.create_workload("W-TEST-3", "Test 3", "payment", status=IdentityStatus.STARTING.value)
    # Before confirmation: blocked
    assert comm_engine.simulate_request("W-TEST-3", "payment-api")["decision"] == "DENY"

    # Confirmation
    identity_mgr.confirm_identity("W-TEST-3", "payment")

    # After confirmation: normal policy allows payment -> payment-api
    res = comm_engine.simulate_request("W-TEST-3", "payment-api")
    assert res["decision"] == "ALLOW"
    assert res["reason"] == "POLICY_ALLOW"

def test_edge_case_4_communicate_during_ambiguity(services):
    """Edge Case 4: Workload tries to communicate during ambiguity."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    identity_mgr.create_workload("W-PRIOR", "Prior", "student", status=IdentityStatus.CONFIRMED.value)
    w = identity_mgr.create_workload("W-AMBIG-4", "Worker 4", "student")
    assert w.status == IdentityStatus.AMBIGUOUS.value

    # Multiple endpoints tested
    for dest in ["database", "student-api", "payment-api"]:
        res = comm_engine.simulate_request("W-AMBIG-4", dest)
        assert res["decision"] == "DENY"
        assert res["reason"] == "IDENTITY_AMBIGUOUS"
        assert res["in_ambiguity_window"] is True

def test_edge_case_5_confirmed_identity_no_matching_policy(services):
    """Edge Case 5: Confirmed identity has no matching policy -> DENY (Reason: NO_POLICY)."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Student has policies for database (DENY) and student-api (ALLOW), but none for admin-api
    identity_mgr.create_workload("W-STUDENT-5", "Student Worker", "student", status=IdentityStatus.CONFIRMED.value)

    res = comm_engine.simulate_request("W-STUDENT-5", "admin-api")
    assert res["decision"] == "DENY"
    assert res["reason"] == "NO_POLICY"

def test_edge_case_6_destination_does_not_exist(services):
    """Edge Case 6: Destination does not exist -> DENY (Reason: INVALID_DESTINATION)."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    identity_mgr.create_workload("W-VALID", "Valid Worker", "payment", status=IdentityStatus.CONFIRMED.value)

    res = comm_engine.simulate_request("W-VALID", "ghost-database-cluster")
    assert res["decision"] == "DENY"
    assert res["reason"] == "INVALID_DESTINATION"

def test_edge_case_7_multiple_communication_attempts_during_ambiguity(services):
    """Edge Case 7: Multiple communication attempts occur during ambiguity window. All must be logged and verified."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]
    verif_svc = services["verification"]
    audit_svc = services["audit"]

    identity_mgr.create_workload("W-OLD-7", "Old 7", "payment", status=IdentityStatus.CONFIRMED.value)
    identity_mgr.create_workload("W-MULTIPLE", "Multi Attempt Worker", "payment")

    # Fire 5 attempts during ambiguity window
    for i in range(5):
        dest = "database" if i % 2 == 0 else "payment-api"
        res = comm_engine.simulate_request("W-MULTIPLE", dest)
        assert res["decision"] == "DENY"
        assert res["in_ambiguity_window"] is True

    # Check audit logs count
    logs = audit_svc.list_logs(workload_id="W-MULTIPLE")
    assert len(logs) == 5
    assert all(l["in_ambiguity_window"] is True for l in logs)

    # Confirm workload
    identity_mgr.confirm_identity("W-MULTIPLE", "student")

    # Retroactive verification must inspect all 5 attempts
    report = verif_svc.verify_ambiguity_window("W-MULTIPLE")
    assert report["result"] == "PASS"
    assert report["total_attempts"] == 5
    assert report["allowed_in_window"] == 0
    assert report["denied_in_window"] == 5
    assert report["wrong_identity_access"] == 0
