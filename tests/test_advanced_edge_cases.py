import pytest
from datetime import datetime, timezone, timedelta
from models.workload import IdentityStatus

def test_attestation_timeout_quarantines_stale_workload(services):
    """Edge Case: Workload startup hangs/times out -> auto-quarantined."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Start time 2 minutes in the past
    two_mins_ago = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    w = identity_mgr.create_workload(
        workload_id="W-STALE",
        name="Stale Worker",
        initial_identity_signal="payment",
        started_at=two_mins_ago
    )
    assert w.status == IdentityStatus.STARTING.value

    # Run attestation timeout check with 60s limit
    quarantined = identity_mgr.check_attestation_timeouts(ttl_seconds=60.0)
    assert any(q["workload_id"] == "W-STALE" for q in quarantined)

    w_updated = identity_mgr.get_workload("W-STALE")
    assert w_updated.status == IdentityStatus.QUARANTINED.value
    assert "Attestation TTL expired" in w_updated.status_reason

    # Communication from quarantined workload must be denied
    res = comm_engine.simulate_request("W-STALE", "payment-api")
    assert res["decision"] == "DENY"
    assert res["reason"] == "IDENTITY_QUARANTINED"

def test_reconnaissance_probe_burst_auto_quarantines(services):
    """Edge Case: Rapid port-scan egress probes during ambiguity trigger automated containment."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Pre-existing established worker to force AMBIGUOUS status on new worker
    identity_mgr.create_workload("W-PRIOR-RECON", "Prior", "admin", status=IdentityStatus.CONFIRMED.value)
    w = identity_mgr.create_workload("W-BURST-ATTACKER", "Burst Attacker", "admin")
    assert w.status == IdentityStatus.AMBIGUOUS.value

    # Fire 5 requests (below threshold)
    for i in range(5):
        res = comm_engine.simulate_request("W-BURST-ATTACKER", "database")
        assert res["decision"] == "DENY"
        assert res["reason"] == "IDENTITY_AMBIGUOUS"

    # 6th request trips the threshold
    res_6th = comm_engine.simulate_request("W-BURST-ATTACKER", "database")
    assert res_6th["decision"] == "DENY"
    assert res_6th["reason"] == "HOSTILE_RECONNAISSANCE_QUARANTINED"

    # Workload is now QUARANTINED
    w_check = identity_mgr.get_workload("W-BURST-ATTACKER")
    assert w_check.status == IdentityStatus.QUARANTINED.value

def test_double_confirmation_immutability(services):
    """Edge Case: Workload cannot be confirmed with a conflicting identity after attestation."""
    identity_mgr = services["identity"]

    w = identity_mgr.create_workload("W-IMMUTABLE", "Worker", "student")
    identity_mgr.confirm_identity("W-IMMUTABLE", "student")

    w_conf = identity_mgr.get_workload("W-IMMUTABLE")
    assert w_conf.status == IdentityStatus.CONFIRMED.value

    # Attempting to re-confirm with same identity is idempotent
    w_reconf = identity_mgr.confirm_identity("W-IMMUTABLE", "student")
    assert w_reconf.confirmed_identity == "student"

    # Attempting to change to 'admin' raises ValueError
    with pytest.raises(ValueError, match="cryptographically immutable"):
        identity_mgr.confirm_identity("W-IMMUTABLE", "admin")

def test_runtime_drift_and_instant_revocation(services):
    """Edge Case: Post-attestation container escape -> identity revoked -> instant block."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Confirmed workload
    identity_mgr.create_workload(
        "W-DRIFT", "Payment Pod", "payment",
        status=IdentityStatus.CONFIRMED.value,
        confirmed_identity="payment"
    )

    # Allowed initially
    res_init = comm_engine.simulate_request("W-DRIFT", "payment-api")
    assert res_init["decision"] == "ALLOW"

    # Revoke due to container compromise
    identity_mgr.revoke_workload("W-DRIFT", reason="Container escape detected by Falco")
    w_revoked = identity_mgr.get_workload("W-DRIFT")
    assert w_revoked.status == IdentityStatus.REVOKED.value

    # Subsequent request is immediately blocked
    res_post = comm_engine.simulate_request("W-DRIFT", "payment-api")
    assert res_post["decision"] == "DENY"
    assert res_post["reason"] == "IDENTITY_REVOKED"

def test_bidirectional_ambiguity_blocking(services):
    """Edge Case: Workload A (CONFIRMED) calls Workload B (AMBIGUOUS) -> DENY (DESTINATION_AMBIGUOUS)."""
    identity_mgr = services["identity"]
    comm_engine = services["comm"]

    # Workload A is CONFIRMED admin
    identity_mgr.create_workload("W-SRC-ADMIN", "Admin Worker", "admin", status=IdentityStatus.CONFIRMED.value)

    # Workload B is STARTING / AMBIGUOUS
    identity_mgr.create_workload("W-DEST-PEER", "Peer Worker", "student", status=IdentityStatus.STARTING.value)

    # Admin calls ambiguous peer
    res = comm_engine.simulate_request("W-SRC-ADMIN", "W-DEST-PEER")
    assert res["decision"] == "DENY"
    assert res["reason"] == "DESTINATION_AMBIGUOUS"
