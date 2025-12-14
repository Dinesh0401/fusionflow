"""Decision gating for automation actions derived from ML + LLM signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.agents.contracts import LLMResponse


@dataclass
class DecisionResult:
    """Outcome of combining ML risk and LLM analysis."""

    verdict: str  # execute | block | request_human
    ml_risk: float
    llm_response: Optional[LLMResponse]


class DecisionEngine:
    """Apply policy thresholds to ML and LLM signals before automation."""

    def __init__(
        self,
        ml_risk_threshold: float,
        llm_confidence_threshold: float,
        human_in_loop: bool = True,
    ) -> None:
        self.ml_risk_threshold = ml_risk_threshold
        self.llm_confidence_threshold = llm_confidence_threshold
        self.human_in_loop = human_in_loop

    def decide(self, ml_failure_risk: Optional[float], llm_response: Optional[LLMResponse]) -> DecisionResult:
        risk_value = float(ml_failure_risk or 0.0)

        if risk_value < self.ml_risk_threshold:
            return DecisionResult(verdict="execute", ml_risk=risk_value, llm_response=llm_response)

        if llm_response is None:
            verdict = "request_human" if self.human_in_loop else "block"
            return DecisionResult(verdict=verdict, ml_risk=risk_value, llm_response=None)

        if llm_response.is_confident(self.llm_confidence_threshold):
            return DecisionResult(verdict="execute", ml_risk=risk_value, llm_response=llm_response)

        verdict = "request_human" if self.human_in_loop else "block"
        return DecisionResult(verdict=verdict, ml_risk=risk_value, llm_response=llm_response)
