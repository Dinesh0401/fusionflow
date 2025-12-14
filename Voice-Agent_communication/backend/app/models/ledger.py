from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class DecisionRecord(SQLModel, table=True):
    __tablename__ = "decision_ledger"

    decision_id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # LLM Metadata
    provider: str = Field(index=True)
    model: str = Field(index=True)
    prompt_hash: str = Field(index=True)
    schema_version: str = Field(default="v1")
    
    # Metrics
    ml_risk_score: float
    llm_confidence: Optional[float] = None
    
    # Gate Outcome
    gate_verdict: str = Field(index=True)  # "allow" or "block"
    gate_reason: str
    
    # Action
    action_type: Optional[str] = None
    action_params: Optional[str] = None  # JSON stringified parameters if needed
    
    # Validation
    schema_valid: bool = True

    # Post-hoc evaluation
    automation_executed: Optional[bool] = None
    downstream_failure: Optional[bool] = None
