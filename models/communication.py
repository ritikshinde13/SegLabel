from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

@dataclass
class CommunicationRequest:
    id: str
    workload_id: str
    source_identity: str
    destination: str
    identity_status: str
    decision: str
    reason: str
    in_ambiguity_window: bool
    timestamp: str

    def to_dict(self):
        d = asdict(self)
        d["in_ambiguity_window"] = bool(self.in_ambiguity_window)
        return d

@dataclass
class AuditLog:
    request_id: str
    workload_id: str
    source: str
    destination: str
    identity_at_decision: str
    identity_status: str
    decision: str
    reason: str
    timestamp: str
    in_ambiguity_window: bool
    id: Optional[int] = None

    def to_dict(self):
        d = asdict(self)
        d["in_ambiguity_window"] = bool(self.in_ambiguity_window)
        return d

@dataclass
class VerificationResult:
    workload_id: str
    window_start: str
    window_end: str
    total_attempts: int
    allowed_in_window: int
    denied_in_window: int
    wrong_identity_access: int
    result: str
    summary: str
    verified_at: str
    flagged_requests: Optional[List[Dict[str, Any]]] = None
    id: Optional[int] = None

    def to_dict(self):
        d = asdict(self)
        return d
