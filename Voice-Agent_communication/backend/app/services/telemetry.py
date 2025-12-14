import logging

from ..models import DecisionRecord

logger = logging.getLogger("vocaverse.telemetry")


async def emit_gate_event(record: DecisionRecord) -> None:
    """Emit a structured telemetry event for a gate verdict."""

    extra = {
        "decision_id": str(record.decision_id),
        "provider": record.provider,
        "model": record.model,
        "prompt_hash": record.prompt_hash,
        "verdict": record.gate_verdict,
        "reason": record.gate_reason,
        "ml_risk_score": record.ml_risk_score,
        "llm_confidence": record.llm_confidence,
    }

    level = logging.WARNING if record.gate_verdict.lower() == "block" else logging.INFO
    logger.log(level, "decision_gate.%s", record.gate_verdict.lower(), extra=extra)
*** End Patch