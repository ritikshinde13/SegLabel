import pytest
from models.workload import IdentityStatus

def test_ambiguous_workload_cannot_communicate(services):
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Pre-existing workload
    identity_mgr.create_workload("W-OLD", "Old Worker", "payment", status=IdentityStatus.CONFIRMED.value)
    # Reused signal -> AMBIGUOUS
    w_new = identity_mgr.create_workload("W-NEW", "New Worker", "payment")
    assert w_new.status == IdentityStatus.AMBIGUOUS.value

    # Attempt to access database
    res1 = comm_engine.simulate_request("W-NEW", "database")
    assert res1["decision"] == "DENY"
    assert res1["reason"] == "IDENTITY_AMBIGUOUS"
    assert res1["in_ambiguity_window"] is True

    # Attempt to access payment-api (even though payment normally has ALLOW)
    res2 = comm_engine.simulate_request("W-NEW", "payment-api")
    assert res2["decision"] == "DENY"
    assert res2["reason"] == "IDENTITY_AMBIGUOUS"
    assert res2["in_ambiguity_window"] is True

def test_starting_workload_cannot_communicate(services):
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Fresh workload without reuse -> STARTING
    w_start = identity_mgr.create_workload("W-START", "Fresh Worker", "admin")
    assert w_start.status == IdentityStatus.STARTING.value

    # All communication during starting phase is denied
    res = comm_engine.simulate_request("W-START", "database")
    assert res["decision"] == "DENY"
    assert res["reason"] == "IDENTITY_AMBIGUOUS"
    assert res["in_ambiguity_window"] is True

def test_communication_after_confirmation(services):
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Setup ambiguous workload claiming payment
    identity_mgr.create_workload("W-0", "Prior", "payment", status=IdentityStatus.CONFIRMED.value)
    identity_mgr.create_workload("W-TEST", "Test Worker", "payment")

    # While ambiguous: denied
    assert comm_engine.simulate_request("W-TEST", "payment-api")["decision"] == "DENY"

    # Confirm identity as student
    identity_mgr.confirm_identity("W-TEST", "student")

    # Attempt database access -> student policy DENIES
    res_db = comm_engine.simulate_request("W-TEST", "database")
    assert res_db["decision"] == "DENY"
    assert res_db["reason"] == "POLICY_DENY"
    assert res_db["in_ambiguity_window"] is False

    # Attempt student-api access -> student policy ALLOWS
    res_api = comm_engine.simulate_request("W-TEST", "student-api")
    assert res_api["decision"] == "ALLOW"
    assert res_api["reason"] == "POLICY_ALLOW"
    assert res_api["in_ambiguity_window"] is False

def test_audit_logs_creation(services):
    identity_mgr = services["identity"]
    comm_engine = services["comm"]
    audit_svc = services["audit"]

    identity_mgr.create_workload("W-AUDIT", "Audit Test Worker", "student", status=IdentityStatus.CONFIRMED.value)
    comm_engine.simulate_request("W-AUDIT", "student-api")
    comm_engine.simulate_request("W-AUDIT", "database")

    logs = audit_svc.list_logs(workload_id="W-AUDIT")
    assert len(logs) == 2

    # Verify log fields
    log_api = next(l for l in logs if l["destination"] == "student-api")
    assert log_api["decision"] == "ALLOW"
    assert log_api["identity_at_decision"] == "student"
    assert log_api["request_id"].startswith("REQ-")

    log_db = next(l for l in logs if l["destination"] == "database")
    assert log_db["decision"] == "DENY"
    assert log_db["reason"] == "POLICY_DENY"
