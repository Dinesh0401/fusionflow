from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

from ..schemas.llm import LLMDecision


class GateVerdict(str, Enum):
    allow = "allow"
    block = "block"


@dataclass(slots=True)
class GateEvaluationInput:
    ml_risk_score: float
    llm_decision: Optional[LLMDecision]
    decision_type: Optional[str] = None
    schema_valid: bool = True


@dataclass(slots=True)
class GateEvaluationResult:
    verdict: GateVerdict
    reason: str


class DecisionGate:
    """Deterministic control layer to approve or block downstream automation."""

    def __init__(self, *, ml_risk_threshold: float, llm_confidence_threshold: float, blocked_providers: Iterable[str] | None = None, blocked_models: Iterable[str] | None = None) -> None:
        self._ml_risk_threshold = ml_risk_threshold
        self._llm_confidence_threshold = llm_confidence_threshold
        self._blocked_providers = {provider.lower() for provider in (blocked_providers or [])}
        self._blocked_models = {model.lower() for model in (blocked_models or [])}

    def evaluate(self, gate_input: GateEvaluationInput) -> GateEvaluationResult:
        if gate_input.schema_valid is False:
            return GateEvaluationResult(GateVerdict.block, "schema_invalid")

        if gate_input.llm_decision is None:
            return GateEvaluationResult(GateVerdict.block, "missing_llm_decision")

        provider = gate_input.llm_decision.provider.lower()
        model = gate_input.llm_decision.model.lower()

        if provider in self._blocked_providers:
            return GateEvaluationResult(GateVerdict.block, "provider_blocked")

        if model in self._blocked_models:
            return GateEvaluationResult(GateVerdict.block, "model_blocked")

        if gate_input.ml_risk_score >= self._ml_risk_threshold:
            return GateEvaluationResult(GateVerdict.block, "ml_risk_threshold_exceeded")

        if gate_input.llm_decision.confidence < self._llm_confidence_threshold:
            return GateEvaluationResult(GateVerdict.block, "llm_confidence_below_threshold")

        return GateEvaluationResult(GateVerdict.allow, "allowed")
