import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Tuple, Optional

SPIFFE_TRUST_DOMAIN = "cluster.local"
SPIFFE_ISSUER = "spire-server.internal"
DEFAULT_SECRET_KEY = "seglabel-spiffe-cluster-signing-key-production"

def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64_decode(s: str) -> bytes:
    padding = len(s) % 4
    if padding:
        s += "=" * (4 - padding)
    return base64.urlsafe_b64decode(s.encode("utf-8"))

class SpiffeService:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = (secret_key or DEFAULT_SECRET_KEY).encode("utf-8")

    def generate_spiffe_id(self, identity: str, namespace: str = "production") -> str:
        """Constructs a compliant SPIFFE ID."""
        clean_id = identity.strip().lower().replace(" ", "-")
        return f"spiffe://{SPIFFE_TRUST_DOMAIN}/ns/{namespace}/sa/{clean_id}"

    def issue_svid(
        self,
        workload_id: str,
        identity: str,
        ttl_seconds: int = 3600,
        namespace: str = "production"
    ) -> Dict[str, Any]:
        """
        Issues a cryptographically signed SPIFFE JWT SVID for a workload.
        """
        spiffe_id = self.generate_spiffe_id(identity, namespace=namespace)
        now = int(time.time())

        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        payload = {
            "sub": spiffe_id,
            "iss": SPIFFE_ISSUER,
            "aud": [SPIFFE_TRUST_DOMAIN],
            "workload_id": workload_id,
            "identity": identity,
            "iat": now,
            "exp": now + ttl_seconds
        }

        header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        sig_b64 = _b64_encode(sig)

        raw_token = f"{header_b64}.{payload_b64}.{sig_b64}"

        return {
            "workload_id": workload_id,
            "spiffe_id": spiffe_id,
            "identity": identity,
            "token": raw_token,
            "issued_at": now,
            "expires_at": now + ttl_seconds,
            "issuer": SPIFFE_ISSUER
        }

    def verify_svid(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Verifies cryptographic integrity and validity of a SPIFFE JWT SVID.
        Returns: (is_valid, claims_dict, reason)
        """
        try:
            parts = token.strip().split(".")
            if len(parts) != 3:
                return False, None, "INVALID_TOKEN_FORMAT: SVID must contain exactly 3 segments"

            header_b64, payload_b64, sig_b64 = parts
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()

            provided_sig = _b64_decode(sig_b64)
            if not hmac.compare_digest(expected_sig, provided_sig):
                return False, None, "CRYPTOGRAPHIC_SIGNATURE_MISMATCH: Forged or tampered SVID token"

            payload = json.loads(_b64_decode(payload_b64).decode("utf-8"))
            now = int(time.time())

            if "exp" in payload and payload["exp"] < now:
                return False, payload, "SVID_EXPIRED: Token expiration time exceeded"

            if payload.get("iss") != SPIFFE_ISSUER:
                return False, payload, f"UNTRUSTED_ISSUER: Expected {SPIFFE_ISSUER}, got {payload.get('iss')}"

            if not payload.get("sub", "").startswith(f"spiffe://{SPIFFE_TRUST_DOMAIN}/"):
                return False, payload, "INVALID_SPIFFE_TRUST_DOMAIN"

            return True, payload, "SVID_VALIDATED"
        except Exception as e:
            return False, None, f"TOKEN_PARSE_ERROR: {str(e)}"
