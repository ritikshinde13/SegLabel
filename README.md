# SegLabel — Workload Identity Ambiguity Window in Microsegmentation

> A Zero Trust Microsegmentation Engine that protects workloads during startup by eliminating the **Identity Ambiguity Window**, enforcing **Fail-Closed Default Deny**, and executing **Retroactive Cryptographic Verification**.

> [!IMPORTANT]
> **Single Unified Localhost Server**: The entire SegLabel application runs on **exactly one port**:
> 🌐 **http://localhost:5050**
> Every module (3D Topology Command Center, Workloads, Policies, Traffic Simulator, Forensics, Audit, SPIFFE Attestation, Attack Lab, and Compliance) is served from this single localhost endpoint with one command: `python app.py`.

---

## 1. Project Overview

In modern cloud-native and Kubernetes environments, microsegmentation relies on assigning cryptographic identities or network labels to workloads (e.g., SPIFFE IDs, ServiceAccounts, pod labels, container metadata). 

However, during workload startup, auto-scaling, container churn, or IP reuse, there exists a vulnerability window: **The Workload Identity Ambiguity Window**. Before an identity is attested, a new or compromised container may report a reused or unconfirmed identity. Naive policy engines that trust this initial signal allow unauthorized lateral movement.

**SegLabel** is a complete, working simulation of a Zero Trust microsegmentation policy engine. It guarantees that:
1. If a workload's identity is **STARTING** or **AMBIGUOUS**, all ingress and egress communication is strictly **DENIED** (`IDENTITY_AMBIGUOUS`).
2. Reused identity signals are detected immediately upon workload registration.
3. Once an identity is confirmed and attested (**CONFIRMED**), normal fine-grained microsegmentation policies apply.
4. After confirmation, the engine runs **Retroactive Security Verification** over the ambiguity window $[t_{\text{started}}, t_{\text{confirmed}}]$ to mathematically prove that **zero** requests were permitted based on an ambiguous identity.

---

## 2. Problem Statement & Threat Model

### The Danger of the Ambiguity Window

```text
Time t0 (Startup)              Time t1 (Collision)            Time t2 (Attestation)
+-------------------------+    +-------------------------+    +-------------------------+
| Workload W-NEW starts   |    | W-NEW claims: 'payment' |    | Attestation resolves:   |
| Status: STARTING        | -> | Old owner: W-OLD        | -> | True identity: 'student'|
| Identity unconfirmed    |    | Naive policy: ALLOW DB! |    | Real policy: DENY DB!   |
+-------------------------+    +-------------------------+    +-------------------------+
                                        ▲
                                        │ CRITICAL BREACH WINDOW!
                                        │ If policy engine trusts unconfirmed signal,
                                        │ an untrusted student worker accesses the database!
```

### Attack Vectors Addressed

* **Ephemeral Identity Spoofing / Confused Deputy**: An untrusted workload claims an initial identity of a privileged service (e.g., `payment` or `admin`).
* **Container IP / Signal Recycled Collision**: Fast pod churn recycles an IP or node token previously associated with a sensitive workload before cryptographic handshakes complete.
* **Race Condition in Label Propagation**: Egress traffic initiated before orchestration labels and identity sidecars synchronize.

---

## 3. Architecture

```text
+-------------------------------------------------------------------------------+
|                             Flask Web Application                             |
|          (Cybersecurity Dashboard • REST APIs • 1-Click Demo Engine)           |
+---------------------------------------+---------------------------------------+
                                        |
     +----------------------------------+----------------------------------+
     |                                  |                                  |
+----v--------------------+   +---------v--------------+   +---------------v----+
|    Identity Manager     |   |     Policy Engine      |   |    Retroactive     |
| - Lifecycle Transitions |   | - Service Registry     |   |  Verifier Engine   |
| - Collision Detection   |   | - Matrix Evaluation    |   | - Window Inspector |
| - Attestation / Confirm |   | - Fail-Closed Rules    |   | - Breach Detection |
+------------+------------+   +---------+--------------+   +---------------+----+
             |                          |                                  |
             +------------+-------------+----------------------------------+
                          |
              +-----------v------------+
              |  Communication Engine  |
              | - Fail-Closed Enforcer |
              | - Audit Trail Recorder |
              +-----------+------------+
                          |
              +-----------v------------+
              |    SQLite Database     |
              | (Workloads, Policies,  |
              |  Requests, Audit, RVA) |
              +------------------------+
```

---

## 4. Main Security Invariants

1. **Fail-Closed Default Deny**: During `STARTING` or `AMBIGUOUS` states, all communication attempts are denied unconditionally with reason `IDENTITY_AMBIGUOUS`.
2. **Never Trust Reused Signals**: If an identity signal was previously claimed by another workload, status is immediately marked `AMBIGUOUS`.
3. **Immutable Audit Logging**: Every single decision, whether in or out of the ambiguity window, is recorded with identity, destination, decision, reason, and window correlation.
4. **Retroactive Ambiguity Verification**: After attestation, the verifier inspects $[t_{\text{started}}, t_{\text{confirmed}}]$.
   * $\text{Allowed During Window} = 0$
   * $\text{Wrong Identity Access} = 0$
   * Any violation immediately triggers **`RESULT: FAIL ✗`** and isolates the compromised request IDs.

---

## 5. Workload Lifecycle State Machine

```text
          [ Workload Starts ]
                   │
                   ▼
         ┌───────────────────┐
         │     STARTING      │ (Fail-Closed: DENY)
         └─────────┬─────────┘
                   │
         Identity collision?
          ├── YES ──► ┌───────────────────┐
          │           │     AMBIGUOUS     │ (Fail-Closed: DENY)
          │           └─────────┬─────────┘
          └── NO ───────────────┤
                                │ Attestation / Confirmation
                                ▼
                      ┌───────────────────┐
                      │     CONFIRMED     │ (Apply Normal Policy)
                      └─────────┬─────────┘
                                │
                                ▼
               [ Run Retroactive Verification ]
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
         [ PASS ✓ ]                        [ FAIL ✗ ]
    (0 Window Allows)                 (≥1 Window Allows)
```

---

## 6. Database Schema

The system uses SQLite (`seglabel.db`) with full relational constraints:

* **`workloads`**: `id` (PK), `name`, `initial_identity_signal`, `current_identity`, `confirmed_identity`, `status` (`STARTING`, `AMBIGUOUS`, `CONFIRMED`), `status_reason`, `started_at`, `confirmed_at`, `created_at`.
* **`identity_events`**: `id` (PK), `workload_id` (FK), `event_type`, `old_status`, `new_status`, `identity_signal`, `details`, `timestamp`.
* **`users`**: `id` (PK), `username` (UNIQUE), `password_hash` (Werkzeug secure hash), `created_at`, `is_active`.
* **`destinations`**: `name` (PK), `description`, `category`.
* **`policies`**: `id` (PK), `source_identity`, `destination`, `action` (`ALLOW`/`DENY`), `description`, `created_at`, `UNIQUE(source_identity, destination)`.
* **`communication_requests`**: `id` (PK), `workload_id` (FK), `source_identity`, `destination`, `identity_status`, `decision`, `reason`, `in_ambiguity_window`, `timestamp`.
* **`audit_logs`**: `id` (PK), `request_id` (FK), `workload_id`, `source`, `destination`, `identity_at_decision`, `identity_status`, `decision`, `reason`, `in_ambiguity_window`, `timestamp`.
* **`verification_results`**: `id` (PK), `workload_id` (FK), `window_start`, `window_end`, `total_attempts`, `allowed_in_window`, `denied_in_window`, `wrong_identity_access`, `result` (`PASS`/`FAIL`), `summary`, `flagged_requests_json`, `verified_at`.

---

## 7. REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/stats` | High-level metrics (fleet counts, requests, passes, failures). |
| `GET` | `/api/workloads` | List all registered workloads. |
| `POST` | `/api/workloads` | Register a new workload (`id`, `name`, `initial_identity_signal`). |
| `GET` | `/api/workloads/<id>` | Workload details, lifecycle events, and audit records. |
| `POST` | `/api/workloads/<id>/confirm` | Attest confirmed identity (`confirmed_identity`). Closes window & triggers verifier. |
| `POST` | `/api/workloads/<id>/communication` | Simulate communication attempt (`destination`). |
| `POST` | `/api/workloads/<id>/verify` | Run retroactive ambiguity window verification. |
| `GET` | `/api/workloads/<id>/audit` | Fetch audit logs for a workload. |
| `GET` | `/api/audit` | Query audit trail with filters (`workload_id`, `decision`, `in_ambiguity_window`). |
| `GET` | `/api/policies` | List all microsegmentation policies. |
| `POST` | `/api/policies` | Create or update a policy rule. |
| `DELETE` | `/api/policies/<id>` | Delete a policy rule. |
| `GET` | `/api/destinations` | List registered service destinations. |
| `POST` | `/api/destinations` | Add a new service destination. |
| `POST` | `/api/demo/run` | Execute the official 8-step security validation demo. |
| `POST` | `/api/demo/tamper` | Inject a synthetic bypass ALLOW inside ambiguity window (tests FAIL detection). |
| `POST` | `/api/reset` | Reset database to clean seed state. |

---

## 8. Installation & Setup

### Prerequisites
* Python 3.11+
* pip

### Installation

```bash
# Clone or navigate to the repository directory
cd seglabel

# Initialize virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 9. Running the Application (Unified Single Localhost Server)

SegLabel runs as a **single, unified server on one port** (`5050`). Every feature, UI page, and REST API operates under this single server:

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the unified Flask application
python app.py
```

Open your browser and navigate to:
```text
http://localhost:5050
```

### 🌐 Unified Localhost Navigation Map (Port 5050)

All features are accessible from the same origin and port:
* **Command Center & 3D Topology**: [http://localhost:5050/](http://localhost:5050/)
* **Workload & Server Inventory**: [http://localhost:5050/workloads](http://localhost:5050/workloads)
* **Zero-Trust Traffic Simulator**: [http://localhost:5050/simulator](http://localhost:5050/simulator)
* **Security Policies Matrix**: [http://localhost:5050/policies](http://localhost:5050/policies)
* **Forensics & Audit Log**: [http://localhost:5050/audit](http://localhost:5050/audit)
* **Retroactive Verification Engine**: [http://localhost:5050/verification](http://localhost:5050/verification)
* **Identity Lifecycle Events**: [http://localhost:5050/events](http://localhost:5050/events)
* **Threat Matrix & Attack Lab**: [http://localhost:5050/attacks](http://localhost:5050/attacks)
* **NIST SP 800-207 Compliance**: [http://localhost:5050/compliance](http://localhost:5050/compliance)
* **REST APIs**: `http://localhost:5050/api/...`

Unauthenticated requests will automatically be routed to the **Secure Access Login Portal** (`/login`).

### Operator Authentication & Demo Credentials

| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **Username** | `admin` | Configurable via `SEG_LABEL_ADMIN_USERNAME` |
| **Password** | `SegLabel@2026!` | Configurable via `SEG_LABEL_ADMIN_PASSWORD` |
| **Password Storage** | Werkzeug Cryptographic Hash | Passwords hashed using scrypt/pbkdf2; never plaintext |
| **Session Security** | HTTP-only Cookies | Protected with HMAC session signing (`SECRET_KEY`) |

To sign out, click the **Operator Profile** / **Sign Out** button in the dashboard top navigation bar.

---

## 10. Running Tests

The test suite covers 100% of the project requirements, including all 10 core test specifications and 7 edge cases:

```bash
# Run tests with pytest
python -m pytest -v
```

### Test Coverage Summary:
* `tests/test_auth.py`: Operator authentication, session guards, password hashing, login form/AJAX, and logout.
* `tests/test_identity.py`: Startup states, identity reuse collision detection, attestation.
* `tests/test_policy.py`: Normal policy rules, unknown destinations, unregistered identities, default deny.
* `tests/test_communication.py`: Zero Trust ambiguity blocking, post-confirmation traffic, audit logs.
* `tests/test_verification.py`: Retroactive ambiguity window audit, safe PASS verification, breach FAIL detection.
* `tests/test_ui.py`: UI page rendering, status indicators, navigation.
* `tests/test_edge_cases.py`: Identity collisions, edge cases, and synthetic tamper testing.
* `tests/test_demo.py`: Automated 8-step security demo scenario assertions.
* `tests/test_api.py`: Full REST API route validation.

---

## 11. Security Demo Walkthrough

Click the prominent **"▶ Run Security Demo"** button on the dashboard or execute via cURL:

```bash
curl -X POST http://localhost:5050/api/demo/run
```

### Automated 8-Step Flow:

1. **Step 1: Create W-OLD**
   * Identity: `payment`
   * Status: `CONFIRMED`
   * Role: Pre-existing established worker.
2. **Step 2: Create W-NEW**
   * Initial signal claimed: `payment`
   * Identity reuse detected: W-NEW claims `payment` which was previously owned by `W-OLD`.
   * Status: **`AMBIGUOUS`**
   * Reason: `"Identity signal reused by another workload (previous owner: W-OLD)"`.
3. **Step 3: Attempt W-NEW ➔ `database`**
   * Decision: **`DENY`**
   * Reason: **`IDENTITY_AMBIGUOUS`**
4. **Step 4: Attempt W-NEW ➔ `payment-api`**
   * **Critical Security Check**: Even though `payment` identity has explicit `ALLOW` permissions to `payment-api`, W-NEW is **`DENIED`** because its identity is unconfirmed!
5. **Step 5: Confirm W-NEW ➔ `student`**
   * Attestation finishes. True identity is confirmed as `student`.
   * Status: **`CONFIRMED`**. Ambiguity window is now closed.
6. **Step 6: Attempt W-NEW ➔ `database`**
   * Decision: **`DENY`**
   * Reason: **`POLICY_DENY`** (`student -> database = DENY`).
7. **Step 7: Attempt W-NEW ➔ `student-api`**
   * Decision: **`ALLOW`**
   * Reason: **`POLICY_ALLOW`** (`student -> student-api = ALLOW`).
8. **Step 8: Run Retroactive Security Verification**
   * Ambiguity window is inspected.
   * `Allowed During Window = 0`
   * `Wrong-Identity Access = 0`
   * **`RESULT: PASS ✓`**

### Verifier Output Example:

```text
====================================
RETROACTIVE SECURITY VERIFICATION
====================================

Workload: W-NEW (New Ingestion Worker)
Ambiguity Window: 2026-09-05T07:20:15.703678+00:00 -> 2026-09-05T07:20:15.717952+00:00
Window Status: CLOSED (Confirmed)
Confirmed Identity: student

Communication Attempts: 2
Allowed During Window: 0
Denied During Window: 2

Wrong-Identity Access: 0

RESULT: PASS ✓

No communication was permitted based on an incorrect or ambiguous identity.
```

---

## 12. Edge Cases Handled

| Edge Case | Description | Handled Behavior |
| :--- | :--- | :--- |
| **Edge Case 1** | Workload has completely unknown identity | Denied during startup (`IDENTITY_AMBIGUOUS`); if confirmed with unknown identity, denied (`UNKNOWN_IDENTITY`). |
| **Edge Case 2** | Identity signal is reused from another workload | Detected on creation, status marked `AMBIGUOUS`, clear warning displayed, all traffic blocked. |
| **Edge Case 3** | Identity becomes confirmed | Workload status transitions to `CONFIRMED`, ambiguity window closes, normal policy applies immediately. |
| **Edge Case 4** | Workload tries to communicate during ambiguity | Blocked with `DENY` and reason `IDENTITY_AMBIGUOUS`. |
| **Edge Case 5** | Confirmed identity has no matching policy for destination | Enforces Default Deny: `DENY` with reason `NO_POLICY`. |
| **Edge Case 6** | Destination does not exist in service registry | Blocked with `DENY` and reason `INVALID_DESTINATION`. |
| **Edge Case 7** | Multiple communication attempts occur during ambiguity window | Every request logged with timestamps and inspected during retroactive verification. |
| **Edge Case 8** | Synthetic bypass breach injected inside ambiguity window | Retroactive verifier detects unauthorized allow, flags **`FAIL ✗`**, and outputs offending request IDs. |
| **Edge Case 9** | Workload startup hangs / times out past TTL | Scanned and automatically transitioned to `QUARANTINED` with reason `Attestation TTL expired`. Egress blocked. |
| **Edge Case 10** | High-frequency egress probe burst during ambiguity | Rate limiter detects hostile reconnaissance (>5 attempts), auto-quarantines workload (`HOSTILE_RECONNAISSANCE_QUARANTINED`). |
| **Edge Case 11** | Confirmed workload attempts second conflicting confirmation | Enforces cryptographic immutability; conflicting identity transition rejected with error. |
| **Edge Case 12** | Post-attestation container escape / runtime drift | Identity revoked (`REVOKED`), immediately severing all network communications. |
| **Edge Case 13** | Egress towards an ambiguous or starting peer destination | Bidirectional Zero Trust enforced; traffic blocked with `DESTINATION_AMBIGUOUS`. |

---

## 13. Beyond PRD: Next-Generation Features

SegLabel implements several cloud-native security capabilities beyond standard requirements:

1. **Cryptographic SPIFFE / SPIRE Attestation Engine (`/attacks`)**:
   * Issues cryptographically signed HMAC-SHA256 JWT SVIDs with standard claims (`spiffe://cluster.local/ns/production/sa/...`).
   * Validates signatures, expirations, and issuers; detects forged or tampered SVID tokens with instant rejection.
2. **Interactive Attack Scenario Playground (`/attacks`)**:
   * **Scenario 1**: Fast IP Churn & Reused Signal Attack.
   * **Scenario 2**: Hostile Reconnaissance Burst & Automated Containment.
   * **Scenario 3**: Cryptographic SVID Forgery & Tamper Rejection.
   * **Scenario 4**: Post-Attestation Runtime Drift & Immediate Revocation.
3. **eBPF & Cilium NetworkPolicy Exporters (`/compliance`)**:
   * Generates live **CiliumNetworkPolicy (CNP)** YAML matching the active policy matrix.
   * Generates standard **Kubernetes NetworkPolicy** manifests with Default-Deny.
   * Generates an **eBPF `sock_ops` C filter** snippet demonstrating kernel-level transport drops during the ambiguity window.
4. **NIST SP 800-207 Zero Trust Scorecard (`/compliance`)**:
   * Real-time posture scorecard evaluating compliance across all 4 Zero Trust architecture pillars.
   * One-click download of the cryptographic Zero Trust Security Audit Report in Markdown.

