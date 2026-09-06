from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

class IdentityStatus(str, Enum):
    STARTING = "STARTING"
    AMBIGUOUS = "AMBIGUOUS"
    CONFIRMED = "CONFIRMED"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"

@dataclass
class Workload:
    id: str
    name: str
    initial_identity_signal: str
    current_identity: str
    status: str
    started_at: str
    confirmed_identity: Optional[str] = None
    status_reason: Optional[str] = None
    confirmed_at: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class IdentityEvent:
    workload_id: str
    event_type: str
    timestamp: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    identity_signal: Optional[str] = None
    details: Optional[str] = None
    id: Optional[int] = None

    def to_dict(self):
        return asdict(self)
