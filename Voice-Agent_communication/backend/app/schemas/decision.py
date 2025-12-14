from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DecisionVerdict(str, Enum):
    allow = "allow"
    block = "block"


class DecisionGatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: DecisionVerdict
    reason: str
    ml_risk_score: float = Field(..., ge=0.0, le=1.0)
    llm_confidence: float | None = Field(None, ge=0.0, le=1.0)
    decision_type: str | None = None
    provider: str | None = None
    model: str | None = None
    schema_valid: bool = True
    prompt_hash: str | None = None
