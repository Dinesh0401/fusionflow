"""Canonical alert payload definitions for monitoring backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class AlertPayload:
    """Structured alert payload shared across all backends."""

    pipeline_id: str
    run_id: str
    severity: str  # INFO | WARNING | ERROR | CRITICAL
    title: str
    message: str
    action: str
    metadata: Dict[str, str]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, str]:
        """Serialize to a dictionary for logging or transport."""

        return {
            "pipeline_id": self.pipeline_id,
            "run_id": self.run_id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "action": self.action,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp.isoformat(),
        }
