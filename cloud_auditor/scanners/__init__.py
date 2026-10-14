
"""Shared models for cloud infrastructure scanners."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Finding:
    """Represents a cloud resource that may need attention."""

    provider: str
    resource_type: str
    resource_id: str
    region: str
    reason: str = ""
    estimated_monthly_savings: float = 0.0
    cleanup_action: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    severity: str = "low"
    account_or_project: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert a finding to a dictionary for reports."""
        return asdict(self)
