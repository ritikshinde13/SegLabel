import pytest

def test_demo_scenario_completes_successfully(services):
    demo_svc = services["demo"]
    result = demo_svc.run_security_demo()

    assert result["success"] is True
    assert len(result["steps"]) == 8

    steps = result["steps"]

    # Step 1: W-OLD confirmed
    assert steps[0]["step"] == 1
    assert steps[0]["workload_id"] == "W-OLD"
    assert steps[0]["status"] == "CONFIRMED"

    # Step 2: W-NEW ambiguous due to reuse
    assert steps[1]["step"] == 2
    assert steps[1]["workload_id"] == "W-NEW"
    assert steps[1]["status"] == "AMBIGUOUS"

    # Step 3: W-NEW -> database DENIED
    assert steps[2]["step"] == 3
    assert steps[2]["destination"] == "database"
    assert steps[2]["decision"] == "DENY"
    assert steps[2]["reason"] == "IDENTITY_AMBIGUOUS"

    # Step 4: W-NEW -> payment-api DENIED
    assert steps[3]["step"] == 4
    assert steps[3]["destination"] == "payment-api"
    assert steps[3]["decision"] == "DENY"
    assert steps[3]["reason"] == "IDENTITY_AMBIGUOUS"

    # Step 5: Confirmed as student
    assert steps[4]["step"] == 5
    assert steps[4]["confirmed_identity"] == "student"
    assert steps[4]["status"] == "CONFIRMED"

    # Step 6: W-NEW -> database DENIED (student policy)
    assert steps[5]["step"] == 6
    assert steps[5]["destination"] == "database"
    assert steps[5]["decision"] == "DENY"
    assert steps[5]["reason"] == "POLICY_DENY"

    # Step 7: W-NEW -> student-api ALLOWED
    assert steps[6]["step"] == 7
    assert steps[6]["destination"] == "student-api"
    assert steps[6]["decision"] == "ALLOW"
    assert steps[6]["reason"] == "POLICY_ALLOW"

    # Step 8: Retroactive verification PASS
    assert steps[7]["step"] == 8
    assert steps[7]["result"] == "PASS"
    assert steps[7]["allowed_during_window"] == 0
    assert steps[7]["wrong_identity_access"] == 0
    assert steps[7]["communication_attempts"] >= 2
