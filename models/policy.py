from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"

@dataclass
class Destination:
    name: str
    description: Optional[str] = None
    category: Optional[str] = "service"

    def to_dict(self):
        return asdict(self)

@dataclass
class Policy:
    source_identity: str
    destination: str
    action: str
    description: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)
