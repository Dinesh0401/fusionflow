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
    """Structured output of executing a plan against a backend.

    Use ``to_json()`` to serialize for persistence. The mutable shape (not
    frozen) lets backends accumulate metrics during execution.
    """
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

    @classmethod
    def from_json(cls, json_str: str) -> "RunResult":
        """Parse a RunResult from its to_json() output. Coerces status back to enum."""
        data = json.loads(json_str)
        data["status"] = RunStatus(data["status"])
        return cls(**data)
