from enum import Enum
import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecommendedActionType(str, Enum):
    retry = "retry"
    tune = "tune"
    skip = "skip"
    alert = "alert"


class RecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: RecommendedActionType = Field(..., description="Action the orchestrator should consider")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Execution parameters for the chosen action")


class LLMDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_summary: str = Field(..., description="Concise explanation of the detected risk or issue")
    likely_root_cause: str = Field(..., description="Primary hypothesis for the underlying problem")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM self-reported confidence between 0 and 1")
    recommended_action: RecommendedAction
    provider: str = Field(..., description="Identifier for the upstream LLM provider")
    model: str = Field(..., description="Model name or version used to generate the response")
    prompt_hash: str = Field(..., description="Deterministic hash of the prompt context for auditing")

    @field_validator("confidence")
    @classmethod
    def _round_confidence(cls, value: float) -> float:
        return round(value, 4)


def compute_prompt_hash(
    *,
    prompt_template_id: str,
    prompt: str,
    tools_schema: dict[str, Any],
    contract_version: str,
) -> str:
    """Return a deterministic hash describing the LLM invocation contract."""

    canonical_payload = {
        "prompt_template_id": prompt_template_id,
        "prompt": prompt.strip(),
        "tools_schema": tools_schema,
        "contract_version": contract_version,
    }

    serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()
