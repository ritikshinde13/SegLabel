import pytest
from services.spiffe_service import SpiffeService
from services.policy_exporter_service import PolicyExporterService
from services.compliance_service import ComplianceService

def test_spiffe_token_issuance_and_verification():
    spiffe = SpiffeService(secret_key="test-signing-key")

    svid = spiffe.issue_svid("W-100", "payment", ttl_seconds=300)
    assert svid["spiffe_id"] == "spiffe://cluster.local/ns/production/sa/payment"
    assert "token" in svid

    # Verify legitimate token
    is_valid, claims, reason = spiffe.verify_svid(svid["token"])
    assert is_valid is True
    assert claims["identity"] == "payment"
    assert claims["workload_id"] == "W-100"
    assert reason == "SVID_VALIDATED"

    # Tampered signature rejected
    tampered_sig = svid["token"][:-4] + "XXXX"
    is_valid_t, _, reason_t = spiffe.verify_svid(tampered_sig)
    assert is_valid_t is False
    assert "SIGNATURE_MISMATCH" in reason_t

    # Expired token rejected
    expired_svid = spiffe.issue_svid("W-EXPIRED", "payment", ttl_seconds=-10)
    is_valid_e, _, reason_e = spiffe.verify_svid(expired_svid["token"])
    assert is_valid_e is False
    assert "EXPIRED" in reason_e

def test_all_attack_scenarios(services):
    demo_svc = services["demo"]

    # Scenario 1: standard 8-step demo
    s1 = demo_svc.run_scenario("ip_churn")
    assert s1["success"] is True
    assert len(s1["steps"]) == 8

    # Scenario 2: reconnaissance burst
    s2 = demo_svc.run_scenario("reconnaissance_burst")
    assert s2["success"] is True
    assert s2["steps"][-1]["status_badge"] == "QUARANTINED"

    # Scenario 3: SPIFFE forgery
    s3 = demo_svc.run_scenario("spiffe_forgery")
    assert s3["success"] is True
    assert any(step["status_badge"] == "FORGERY_BLOCKED" for step in s3["steps"])

    # Scenario 4: runtime drift
    s4 = demo_svc.run_scenario("runtime_drift")
    assert s4["success"] is True
    assert s4["steps"][-1]["reason"] == "IDENTITY_REVOKED"

def test_policy_exporters(services):
    exporter = PolicyExporterService(services["db_path"])

    cilium_yaml = exporter.export_cilium_manifest()
    assert "apiVersion: \"cilium.io/v2\"" in cilium_yaml
    assert "CiliumNetworkPolicy" in cilium_yaml
    assert "payment" in cilium_yaml

    k8s_yaml = exporter.export_k8s_network_policy()
    assert "networking.k8s.io/v1" in k8s_yaml
    assert "NetworkPolicy" in k8s_yaml
    assert "seglabel-default-deny-all" in k8s_yaml

    ebpf_c = exporter.export_ebpf_sock_ops_snippet()
    assert "BPF_PROG_TYPE_SOCK_OPS" in ebpf_c
    assert "seglabel_sock_ops_enforce" in ebpf_c

def test_compliance_scorecard(services):
    comp_svc = ComplianceService(services["db_path"])
    scorecard = comp_svc.get_zero_trust_scorecard()

    assert "overall_score" in scorecard
    assert scorecard["overall_score"] > 80
    assert len(scorecard["pillars"]) == 4

    report_md = comp_svc.generate_markdown_audit_report()
    assert "NIST SP 800-207" in report_md
    assert "Executive Summary" in report_md

def test_api_quarantine_revoke_and_compliance(client):
    # Test quarantine endpoint
    res_create = client.post("/api/workloads", json={"id": "W-API-QUAR", "name": "API Pod", "initial_identity_signal": "test"})
    assert res_create.status_code == 201

    res_q = client.post("/api/workloads/W-API-QUAR/quarantine", json={"reason": "Manual isolation"})
    assert res_q.status_code == 200
    assert res_q.get_json()["status"] == "QUARANTINED"

    # Test revoke endpoint
    res_r = client.post("/api/workloads/W-API-QUAR/revoke", json={"reason": "Compromised pod"})
    assert res_r.status_code == 200
    assert res_r.get_json()["status"] == "REVOKED"

    # Test SPIFFE token generation and attestation via API
    res_token = client.post("/api/workloads/W-API-QUAR/spiffe-token", json={"identity": "student"})
    assert res_token.status_code == 200
    token = res_token.get_json()["token"]

    # Test compliance scorecard endpoint
    res_comp = client.get("/api/compliance/scorecard")
    assert res_comp.status_code == 200
    assert "overall_score" in res_comp.get_json()

    # Test policy export endpoints
    assert client.get("/api/export/cilium").status_code == 200
    assert client.get("/api/export/k8s").status_code == 200
    assert client.get("/api/export/ebpf").status_code == 200

    # Test scenario run endpoint
    res_scen = client.post("/api/scenarios/reconnaissance_burst/run")
    assert res_scen.status_code == 200
    assert res_scen.get_json()["success"] is True
