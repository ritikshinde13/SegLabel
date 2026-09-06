from flask import Blueprint, request, jsonify, current_app
from services.identity_manager import IdentityManager
from services.policy_engine import PolicyEngine
from services.communication_engine import CommunicationEngine
from services.audit_service import AuditService
from services.verification_service import VerificationService
from services.demo_service import DemoService
from database.db import reset_db

api_bp = Blueprint("api", __name__, url_prefix="/api")

def get_services():
    db_path = current_app.config["DATABASE_PATH"]
    return (
        IdentityManager(db_path),
        PolicyEngine(db_path),
        CommunicationEngine(db_path),
        AuditService(db_path),
        VerificationService(db_path),
        DemoService(db_path)
    )

@api_bp.route("/stats", methods=["GET"])
def get_stats():
    identity_mgr, policy_engine, comm_engine, audit_svc, verif_svc, _ = get_services()
    workloads = identity_mgr.list_workloads()
    audit_summary = audit_svc.get_audit_summary()
    verifications = verif_svc.list_verification_results()

    total_workloads = len(workloads)
    ambiguous_workloads = sum(1 for w in workloads if w.status in ("AMBIGUOUS", "STARTING"))
    confirmed_workloads = sum(1 for w in workloads if w.status == "CONFIRMED")
    quarantined_workloads = sum(1 for w in workloads if w.status == "QUARANTINED")
    revoked_workloads = sum(1 for w in workloads if w.status == "REVOKED")

    verif_passes = sum(1 for v in verifications if v["result"] == "PASS")
    verif_fails = sum(1 for v in verifications if v["result"] == "FAIL")

    return jsonify({
        "total_workloads": total_workloads,
        "ambiguous_workloads": ambiguous_workloads,
        "confirmed_workloads": confirmed_workloads,
        "quarantined_workloads": quarantined_workloads,
        "revoked_workloads": revoked_workloads,
        "communication_attempts": audit_summary["total_requests"],
        "allowed_requests": audit_summary["allowed_requests"],
        "denied_requests": audit_summary["denied_requests"],
        "ambiguity_window_requests": audit_summary["ambiguity_window_requests"],
        "ambiguity_window_violations": audit_summary["ambiguity_window_violations"],
        "verification_passes": verif_passes,
        "verification_failures": verif_fails
    })

@api_bp.route("/workloads", methods=["GET"])
def list_workloads():
    identity_mgr, _, _, _, _, _ = get_services()
    workloads = identity_mgr.list_workloads()
    return jsonify([w.to_dict() for w in workloads])

@api_bp.route("/workloads", methods=["POST"])
def create_workload():
    identity_mgr, _, _, _, _, _ = get_services()
    data = request.get_json() or {}

    workload_id = data.get("id") or data.get("workload_id")
    name = data.get("name")
    signal = data.get("initial_identity_signal") or data.get("identity_signal")

    if not workload_id or not name or not signal:
        return jsonify({"error": "Missing required fields: id, name, and initial_identity_signal"}), 400

    try:
        workload = identity_mgr.create_workload(
            workload_id=workload_id.strip(),
            name=name.strip(),
            initial_identity_signal=signal.strip(),
            status=data.get("status"),
            confirmed_identity=data.get("confirmed_identity")
        )
        return jsonify(workload.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@api_bp.route("/workloads/<workload_id>", methods=["GET"])
def get_workload_detail(workload_id: str):
    identity_mgr, _, _, audit_svc, verif_svc, _ = get_services()
    workload = identity_mgr.get_workload(workload_id)
    if not workload:
        return jsonify({"error": f"Workload '{workload_id}' not found"}), 404

    events = identity_mgr.get_identity_events(workload_id)
    audit_logs = audit_svc.list_logs(workload_id=workload_id)
    verifications = verif_svc.list_verification_results(workload_id=workload_id)

    return jsonify({
        "workload": workload.to_dict(),
        "events": [e.to_dict() for e in events],
        "audit_logs": audit_logs,
        "verifications": verifications
    })

@api_bp.route("/workloads/<workload_id>/confirm", methods=["POST"])
def confirm_workload(workload_id: str):
    identity_mgr, _, _, _, verif_svc, _ = get_services()
    data = request.get_json() or {}
    confirmed_id = data.get("confirmed_identity")

    if not confirmed_id:
        return jsonify({"error": "Field 'confirmed_identity' is required"}), 400

    try:
        updated = identity_mgr.confirm_identity(workload_id, confirmed_id.strip())
        # Automatically run retroactive verification after confirmation
        auto_verification = verif_svc.verify_ambiguity_window(workload_id)
        return jsonify({
            "workload": updated.to_dict(),
            "auto_verification": auto_verification
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@api_bp.route("/workloads/<workload_id>/communication", methods=["POST"])
def simulate_communication(workload_id: str):
    _, _, comm_engine, _, _, _ = get_services()
    data = request.get_json() or {}
    destination = data.get("destination")

    if not destination:
        return jsonify({"error": "Field 'destination' is required"}), 400

    try:
        result = comm_engine.simulate_request(workload_id, destination.strip())
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/workloads/<workload_id>/verify", methods=["POST"])
def verify_workload(workload_id: str):
    _, _, _, _, verif_svc, _ = get_services()
    try:
        result = verif_svc.verify_ambiguity_window(workload_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/workloads/<workload_id>/audit", methods=["GET"])
def get_workload_audit(workload_id: str):
    _, _, _, audit_svc, _, _ = get_services()
    logs = audit_svc.list_logs(workload_id=workload_id)
    return jsonify(logs)

@api_bp.route("/audit", methods=["GET"])
def list_all_audit():
    _, _, _, audit_svc, _, _ = get_services()
    workload_id = request.args.get("workload_id")
    decision = request.args.get("decision")
    window_filter = request.args.get("in_ambiguity_window")
    limit = int(request.args.get("limit", 100))

    in_window = None
    if window_filter is not None and window_filter != "":
        in_window = window_filter.lower() in ("true", "1")

    logs = audit_svc.list_logs(
        workload_id=workload_id,
        decision=decision,
        in_ambiguity_window=in_window,
        limit=limit
    )
    return jsonify(logs)

@api_bp.route("/events", methods=["GET"])
def list_identity_events():
    identity_mgr, _, _, _, _, _ = get_services()
    limit = int(request.args.get("limit", 100))
    events = identity_mgr.list_all_identity_events(limit=limit)
    return jsonify(events)


@api_bp.route("/policies", methods=["GET"])
def list_policies():
    _, policy_engine, _, _, _, _ = get_services()
    policies = policy_engine.list_policies()
    return jsonify([p.to_dict() for p in policies])

@api_bp.route("/policies", methods=["POST"])
def create_or_update_policy():
    _, policy_engine, _, _, _, _ = get_services()
    data = request.get_json() or {}
    src = data.get("source_identity")
    dest = data.get("destination")
    action = data.get("action")
    desc = data.get("description")

    if not src or not dest or not action:
        return jsonify({"error": "Fields source_identity, destination, and action are required"}), 400

    try:
        pol = policy_engine.add_policy(src.strip(), dest.strip(), action.strip(), desc)
        return jsonify(pol.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@api_bp.route("/policies/<int:policy_id>", methods=["DELETE"])
def delete_policy(policy_id: int):
    _, policy_engine, _, _, _, _ = get_services()
    success = policy_engine.delete_policy(policy_id)
    if success:
        return jsonify({"message": f"Policy {policy_id} deleted"}), 200
    return jsonify({"error": f"Policy {policy_id} not found"}), 404

@api_bp.route("/destinations", methods=["GET"])
def list_destinations():
    _, policy_engine, _, _, _, _ = get_services()
    dests = policy_engine.list_destinations()
    return jsonify([d.to_dict() for d in dests])

@api_bp.route("/destinations", methods=["POST"])
def add_destination():
    _, policy_engine, _, _, _, _ = get_services()
    data = request.get_json() or {}
    name = data.get("name")
    desc = data.get("description")
    cat = data.get("category", "service")

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    dest = policy_engine.add_destination(name.strip(), desc, cat)
    return jsonify(dest.to_dict()), 201

@api_bp.route("/verifications", methods=["GET"])
def list_verifications():
    _, _, _, _, verif_svc, _ = get_services()
    workload_id = request.args.get("workload_id")
    results = verif_svc.list_verification_results(workload_id=workload_id)
    return jsonify(results)

@api_bp.route("/demo/run", methods=["POST"])
def run_demo():
    _, _, _, _, _, demo_svc = get_services()
    try:
        res = demo_svc.run_security_demo()
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@api_bp.route("/demo/tamper", methods=["POST"])
def inject_tamper():
    """Injects an unsafe ALLOW event inside ambiguity window for demonstration/testing."""
    _, _, comm_engine, _, _, _ = get_services()
    data = request.get_json() or {}
    workload_id = data.get("workload_id", "W-NEW")
    destination = data.get("destination", "database")

    try:
        res = comm_engine.inject_tampered_request(workload_id, destination)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@api_bp.route("/reset", methods=["POST"])
def reset_system():
    db_path = current_app.config["DATABASE_PATH"]
    reset_db(db_path)
    return jsonify({"message": "Database successfully reset to seed defaults."}), 200

@api_bp.route("/workloads/<workload_id>/quarantine", methods=["POST"])
def quarantine_workload(workload_id: str):
    identity_mgr, _, _, _, _, _ = get_services()
    data = request.get_json() or {}
    reason = data.get("reason", "Administrative quarantine command triggered")
    try:
        w = identity_mgr.quarantine_workload(workload_id, reason=reason)
        return jsonify(w.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@api_bp.route("/workloads/<workload_id>/revoke", methods=["POST"])
def revoke_workload(workload_id: str):
    identity_mgr, _, _, _, _, _ = get_services()
    data = request.get_json() or {}
    reason = data.get("reason", "Cryptographic revocation / runtime compromise")
    try:
        w = identity_mgr.revoke_workload(workload_id, reason=reason)
        return jsonify(w.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@api_bp.route("/workloads/check-timeouts", methods=["POST"])
def check_timeouts():
    identity_mgr, _, _, _, _, _ = get_services()
    data = request.get_json() or {}
    ttl = float(data.get("ttl_seconds", 60.0))
    quarantined = identity_mgr.check_attestation_timeouts(ttl_seconds=ttl)
    return jsonify({
        "quarantined_count": len(quarantined),
        "quarantined": quarantined
    }), 200

@api_bp.route("/workloads/<workload_id>/spiffe-token", methods=["POST"])
def issue_spiffe_token(workload_id: str):
    from services.spiffe_service import SpiffeService
    identity_mgr, _, _, _, _, _ = get_services()
    w = identity_mgr.get_workload(workload_id)
    if not w:
        return jsonify({"error": f"Workload {workload_id} not found"}), 404

    data = request.get_json() or {}
    target_identity = data.get("identity", w.initial_identity_signal)
    ttl = int(data.get("ttl_seconds", 3600))

    spiffe_svc = SpiffeService()
    token_data = spiffe_svc.issue_svid(workload_id, target_identity, ttl_seconds=ttl)
    return jsonify(token_data), 200

@api_bp.route("/workloads/<workload_id>/spiffe-attest", methods=["POST"])
def attest_spiffe_token(workload_id: str):
    from services.spiffe_service import SpiffeService
    identity_mgr, _, _, _, verif_svc, _ = get_services()
    data = request.get_json() or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "Missing 'token' in request payload"}), 400

    spiffe_svc = SpiffeService()
    is_valid, claims, reason = spiffe_svc.verify_svid(token)
    if not is_valid:
        return jsonify({
            "error": "SPIFFE SVID verification failed",
            "reason": reason,
            "success": False
        }), 400

    confirmed_id = claims.get("identity")
    try:
        updated_workload = identity_mgr.confirm_identity(workload_id, confirmed_id)
        verification_report = verif_svc.verify_ambiguity_window(workload_id)
        return jsonify({
            "workload": updated_workload.to_dict(),
            "spiffe_claims": claims,
            "verification": verification_report,
            "success": True
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e), "success": False}), 409

@api_bp.route("/export/cilium", methods=["GET"])
def export_cilium():
    from services.policy_exporter_service import PolicyExporterService
    db_path = current_app.config["DATABASE_PATH"]
    exporter = PolicyExporterService(db_path)
    manifest = exporter.export_cilium_manifest()
    return jsonify({"format": "yaml", "kind": "CiliumNetworkPolicy", "manifest": manifest}), 200

@api_bp.route("/export/k8s", methods=["GET"])
def export_k8s():
    from services.policy_exporter_service import PolicyExporterService
    db_path = current_app.config["DATABASE_PATH"]
    exporter = PolicyExporterService(db_path)
    manifest = exporter.export_k8s_network_policy()
    return jsonify({"format": "yaml", "kind": "NetworkPolicy", "manifest": manifest}), 200

@api_bp.route("/export/ebpf", methods=["GET"])
def export_ebpf():
    from services.policy_exporter_service import PolicyExporterService
    db_path = current_app.config["DATABASE_PATH"]
    exporter = PolicyExporterService(db_path)
    code = exporter.export_ebpf_sock_ops_snippet()
    return jsonify({"format": "c", "kind": "bpf_sock_ops", "code": code}), 200

@api_bp.route("/compliance/scorecard", methods=["GET"])
def get_compliance_scorecard():
    from services.compliance_service import ComplianceService
    db_path = current_app.config["DATABASE_PATH"]
    svc = ComplianceService(db_path)
    scorecard = svc.get_zero_trust_scorecard()
    return jsonify(scorecard), 200

@api_bp.route("/compliance/report", methods=["GET"])
def get_compliance_report():
    from services.compliance_service import ComplianceService
    db_path = current_app.config["DATABASE_PATH"]
    svc = ComplianceService(db_path)
    report_md = svc.generate_markdown_audit_report()
    return jsonify({"format": "markdown", "report": report_md}), 200

@api_bp.route("/scenarios/<scenario_id>/run", methods=["POST"])
def run_scenario_route(scenario_id: str):
    _, _, _, _, _, demo_svc = get_services()
    try:
        res = demo_svc.run_scenario(scenario_id)
        return jsonify(res), 200
    except ValueError as e:
        return jsonify({"error": str(e), "success": False}), 404
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500
