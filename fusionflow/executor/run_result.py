"""RunResult: structured output of executing a plan against a backend."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict


class RunStatus(str, Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class RunResult:
    experiment: str
    backend: str
    status: RunStatus
    ir_version: str
    metrics: Dict[str, float] = field(default_factory=dict)
    detail: str = ""

    def to_json(self, indent: int = 2) -> str:
        """Deterministic JSON serialization. Field order is dataclass declaration order."""
        payload = asdict(self)
        payload["status"] = self.status.value  # ensure string, not Enum
        return json.dumps(payload, indent=indent, sort_keys=False)
