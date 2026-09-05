import pytest

def test_seeded_policies_evaluation(services):
    policy_engine = services["policy"]

    # payment -> database = ALLOW
    dec, reason, _ = policy_engine.evaluate("payment", "database")
    assert dec == "ALLOW"
    assert reason == "POLICY_ALLOW"

    # payment -> payment-api = ALLOW
    dec, reason, _ = policy_engine.evaluate("payment", "payment-api")
    assert dec == "ALLOW"
    assert reason == "POLICY_ALLOW"

    # student -> database = DENY
    dec, reason, _ = policy_engine.evaluate("student", "database")
    assert dec == "DENY"
    assert reason == "POLICY_DENY"

    # student -> student-api = ALLOW
    dec, reason, _ = policy_engine.evaluate("student", "student-api")
    assert dec == "ALLOW"
    assert reason == "POLICY_ALLOW"

def test_unknown_destination_denied(services):
    policy_engine = services["policy"]
    dec, reason, _ = policy_engine.evaluate("payment", "non-existent-service")
    assert dec == "DENY"
    assert reason == "INVALID_DESTINATION"

def test_unknown_identity_denied(services):
    policy_engine = services["policy"]
    dec, reason, _ = policy_engine.evaluate("hacker-workload", "database")
    assert dec == "DENY"
    assert reason == "UNKNOWN_IDENTITY"

def test_missing_policy_denied(services):
    policy_engine = services["policy"]
    # 'student' is a known identity, but has no rule for 'admin-api'
    dec, reason, _ = policy_engine.evaluate("student", "admin-api")
    assert dec == "DENY"
    assert reason == "NO_POLICY"

def test_add_and_delete_policy(services):
    policy_engine = services["policy"]
    pol = policy_engine.add_policy("student", "admin-api", "ALLOW", "Special temp grant")
    assert pol.action == "ALLOW"

    dec, reason, _ = policy_engine.evaluate("student", "admin-api")
    assert dec == "ALLOW"

    # Delete policy
    success = policy_engine.delete_policy(pol.id)
    assert success is True

    dec, reason, _ = policy_engine.evaluate("student", "admin-api")
    assert dec == "DENY"
    assert reason == "NO_POLICY"
