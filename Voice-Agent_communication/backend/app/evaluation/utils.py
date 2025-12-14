from __future__ import annotations

from typing import Optional

from ..models import DecisionRecord


def decision_correctness(record: DecisionRecord) -> Optional[bool]:
    """Return True if the automation decision was correct, False if incorrect, None if unknown."""

    verdict = (record.gate_verdict or "").lower()
    if verdict == "allow":
        if record.downstream_failure is None:
            return None
        return not record.downstream_failure
    if verdict == "block":
        if record.automation_executed is None:
            return None
        # Correct when automation was prevented
        return not record.automation_executed
    return None


def is_false_allow(record: DecisionRecord) -> bool:
    verdict = (record.gate_verdict or "").lower()
    return verdict == "allow" and record.downstream_failure is True


def is_false_block(record: DecisionRecord) -> bool:
    verdict = (record.gate_verdict or "").lower()
    return verdict == "block" and record.automation_executed is True
