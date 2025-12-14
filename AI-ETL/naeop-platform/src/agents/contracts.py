"""Contracts and dataclasses for automation agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional


ActionType = Literal["retry", "tune", "skip", "alert", "none"]


@dataclass(frozen=True)
class LLMRecommendedAction:
    """Structured recommendation produced by an LLM-backed agent."""

    type: ActionType
    parameters: Dict[str, str]


@dataclass(frozen=True)
class LLMResponse:
    """Normalized response payload returned by an automation agent."""

    risk_summary: str
    likely_root_cause: str
    confidence: float
    recommended_action: LLMRecommendedAction

    def is_confident(self, threshold: float) -> bool:
        """Indicate whether the LLM confidence exceeds the configured threshold."""

        return self.confidence >= threshold

    def to_dict(self) -> Dict[str, object]:
        return {
            "risk_summary": self.risk_summary,
            "likely_root_cause": self.likely_root_cause,
            "confidence": self.confidence,
            "recommended_action": {
                "type": self.recommended_action.type,
                "parameters": dict(self.recommended_action.parameters),
            },
        }


@dataclass(frozen=True)
class AgentOutput:
    """Complete automation agent result, including raw text for auditing."""

    response: LLMResponse
    raw_text: str

    def to_dict(self) -> Dict[str, object]:
        data = self.response.to_dict()
        data["raw_text"] = self.raw_text
        return data
