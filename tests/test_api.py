import pytest
import json

def test_api_stats(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.get_json()
    assert "total_workloads" in data
    assert "ambiguous_workloads" in data
    assert "communication_attempts" in data

def test_api_workload_lifecycle_and_verification(client):
    # 1. Create established workload
    res1 = client.post("/api/workloads", json={
        "id": "W-API-OLD",
        "name": "API Old",
        "initial_identity_signal": "payment",
        "status": "CONFIRMED",
        "confirmed_identity": "payment"
    })
    assert res1.status_code == 201

    # 2. Create ambiguous workload with reused identity
    res2 = client.post("/api/workloads", json={
        "id": "W-API-NEW",
        "name": "API New",
        "initial_identity_signal": "payment"
    })
    assert res2.status_code == 201
    w_new = res2.get_json()
    assert w_new["status"] == "AMBIGUOUS"

    # 3. Simulate communication during ambiguity window
    res3 = client.post("/api/workloads/W-API-NEW/communication", json={
        "destination": "database"
    })
    assert res3.status_code == 200
    comm = res3.get_json()
    assert comm["decision"] == "DENY"
    assert comm["reason"] == "IDENTITY_AMBIGUOUS"

    # 4. Confirm identity
    res4 = client.post("/api/workloads/W-API-NEW/confirm", json={
        "confirmed_identity": "student"
    })
    assert res4.status_code == 200
    conf = res4.get_json()
    assert conf["workload"]["status"] == "CONFIRMED"
    assert "auto_verification" in conf
    assert conf["auto_verification"]["result"] == "PASS"

    # 5. Simulate post-confirmation request
    res5 = client.post("/api/workloads/W-API-NEW/communication", json={
        "destination": "student-api"
    })
    assert res5.status_code == 200
    assert res5.get_json()["decision"] == "ALLOW"

    # 6. Query audit logs
    res6 = client.get("/api/workloads/W-API-NEW/audit")
    assert res6.status_code == 200
    logs = res6.get_json()
    assert len(logs) >= 2

    # 7. Query verifications
    res7 = client.post("/api/workloads/W-API-NEW/verify")
    assert res7.status_code == 200
    verif = res7.get_json()
    assert verif["result"] == "PASS"

def test_api_policies_crud(client):
    # List policies
    res = client.get("/api/policies")
    assert res.status_code == 200
    initial_count = len(res.get_json())

    # Add policy
    res_add = client.post("/api/policies", json={
        "source_identity": "test-role",
        "destination": "database",
        "action": "ALLOW",
        "description": "Test policy"
    })
    assert res_add.status_code == 201
    pol_id = res_add.get_json()["id"]

    # Delete policy
    res_del = client.delete(f"/api/policies/{pol_id}")
    assert res_del.status_code == 200

def test_api_destinations(client):
    res = client.get("/api/destinations")
    assert res.status_code == 200
    assert len(res.get_json()) >= 4

    res_add = client.post("/api/destinations", json={
        "name": "new-test-api",
        "description": "New test destination",
        "category": "service"
    })
    assert res_add.status_code == 201

def test_api_demo_run(client):
    res = client.post("/api/demo/run")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["steps"]) == 8
    assert data["final_verification"]["result"] == "PASS"

def test_api_reset(client):
    res = client.post("/api/reset")
    assert res.status_code == 200
    assert "reset" in res.get_json()["message"].lower()
