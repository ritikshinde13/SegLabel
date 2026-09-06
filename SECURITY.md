# Security Policy & Architecture Hardening — SegLabel

SegLabel is designed from the ground up as a **Zero Trust Microsegmentation Engine** that eliminates the **Workload Identity Ambiguity Window** during startup and container churn. This document details our security model, defense-in-depth controls, and vulnerability disclosure protocol.

---

## 1. Supported Versions

Security updates and patches are actively maintained for the following versions:

| Version | Supported | Security Maintenance |
| :--- | :---: | :--- |
| `v1.0.x` (Current `main`) | ✅ Yes | Actively patched against OWASP & Zero Trust vulnerabilities |
| `< 1.0.0` | ❌ No | Deprecated development prototypes |

---

## 2. Zero Trust Core Security Guarantees

SegLabel enforces mathematical Zero Trust network microsegmentation:

1. **Fail-Closed Default Deny**:
   * Any workload in `STARTING` or `AMBIGUOUS` state is strictly prohibited from egress/ingress network communication (`IDENTITY_AMBIGUOUS`).
   * No permissions are granted based on unconfirmed or speculative labels.
2. **Reused Identity Signal Collision Containment**:
   * When an unconfirmed workload claims an identity recently owned by another workload, it is immediately quarantined in `AMBIGUOUS` state.
3. **Automated Hostile Reconnaissance Quarantine**:
   * Workloads attempting high-frequency burst probes (>5 denied egress requests) during the ambiguity window are automatically quarantined (`AUTO_QUARANTINE_RECONNAISSANCE`), containing port scanners and lateral movement tools.
4. **Cryptographic SPIFFE / SPIRE Attestation**:
   * Workloads authenticate via HMAC-SHA256 cryptographically signed SVID tokens (`spiffe://cluster.local/ns/production/sa/...`). Token forgery or parameter tampering results in immediate cryptographic rejection.
5. **Retroactive Forensic Verification**:
   * After identity confirmation, the engine computes a mathematical audit over the ambiguity window $[t_{\text{started}}, t_{\text{confirmed}}]$ to prove zero leakage occurred.

---

## 3. Application & Infrastructure Hardening (OWASP Top 10)

| Security Domain | Applied Control | OWASP Reference |
| :--- | :--- | :--- |
| **SQL Injection (SQLi)** | 100% Prepared Statements via SQLite parameterized queries (`?`). Zero raw string formatting. | A03:2021-Injection |
| **Brute Force Mitigation** | Sliding-window IP rate limiting on `/login` (max 8 failed attempts / 60s) returning HTTP 429. | A07:2021-Identification and Authentication Failures |
| **Session Security** | Cryptographic 256-bit `SECRET_KEY`, `HttpOnly`, `SameSite=Lax`, strict session expiration. | A07:2021-Identification and Authentication Failures |
| **Clickjacking & Framing** | Strict `X-Frame-Options: DENY` response header on all routes. | A05:2021-Security Misconfiguration |
| **MIME Sniffing** | `X-Content-Type-Options: nosniff` header on all responses. | A05:2021-Security Misconfiguration |
| **Content Security Policy** | Restrictive `Content-Security-Policy` header limiting script, object, and style evaluation. | A05:2021-Security Misconfiguration |
| **Cross-Site Scripting (XSS)**| Jinja2 autoescaping enabled across all templates + CSP protection. | A03:2021-Injection |
| **Open Redirects** | Path validation and sanitization on all redirection parameters (`next_url`). | A01:2021-Broken Access Control |
| **Denial of Service (DoS)** | Request body payload limits (`MAX_CONTENT_LENGTH = 16MB`) preventing memory exhaustion. | A04:2021-Insecure Design |

---

## 4. Reporting a Vulnerability

If you discover a security vulnerability within SegLabel:

1. **Do not create a public GitHub issue.**
2. Send an email to: `security@seglabel.local` (or repository maintainer).
3. Include:
   * Description of the vulnerability and attack vector.
   * Step-by-step reproduction steps or proof-of-concept (PoC).
   * Affected endpoints or services.
4. The maintainers will respond within **48 hours** with a status assessment and coordinated remediation timeline.
