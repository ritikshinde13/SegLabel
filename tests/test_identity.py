import pytest
from models.workload import IdentityStatus

def test_new_workload_starts_starting(services):
    identity_mgr = services["identity"]
    w = identity_mgr.create_workload("W-1", "Alpha Worker", "student")
    assert w.id == "W-1"
    assert w.status == IdentityStatus.STARTING.value
    assert w.current_identity == "student"
    assert w.confirmed_identity is None
    assert w.confirmed_at is None

def test_reused_identity_detected(services):
    identity_mgr = services["identity"]
    # Establish old workload with payment identity
    w_old = identity_mgr.create_workload(
        "W-OLD",
        "Established Worker",
        "payment",
        status=IdentityStatus.CONFIRMED.value,
        confirmed_identity="payment"
    )
    assert w_old.status == IdentityStatus.CONFIRMED.value

    # Create new workload reporting the same identity signal
    w_new = identity_mgr.create_workload("W-NEW", "New Ingestion Worker", "payment")
    assert w_new.status == IdentityStatus.AMBIGUOUS.value
    assert "reused" in w_new.status_reason.lower()
    assert "W-OLD" in w_new.status_reason

    # Verify identity events
    events = identity_mgr.get_identity_events("W-NEW")
    event_types = [e.event_type for e in events]
    assert "WORKLOAD_STARTED" in event_types
    assert "AMBIGUITY_DETECTED" in event_types

def test_confirm_identity_lifecycle(services):
    identity_mgr = services["identity"]
    # Create ambiguous workload
    identity_mgr.create_workload("W-1", "Worker 1", "payment", status=IdentityStatus.CONFIRMED.value)
    w2 = identity_mgr.create_workload("W-2", "Worker 2", "payment")
    assert w2.status == IdentityStatus.AMBIGUOUS.value

    # Confirm identity as student
    confirmed = identity_mgr.confirm_identity("W-2", "student")
    assert confirmed.status == IdentityStatus.CONFIRMED.value
    assert confirmed.confirmed_identity == "student"
    assert confirmed.current_identity == "student"
    assert confirmed.confirmed_at is not None

    events = identity_mgr.get_identity_events("W-2")
    assert any(e.event_type == "IDENTITY_CONFIRMED" for e in events)
