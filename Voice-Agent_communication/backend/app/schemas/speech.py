from typing import Any

from pydantic import BaseModel

from .decision import DecisionGatePayload
from .llm import LLMDecision


class SpeechProcessRequest(BaseModel):
    session_id: str
    audio_format: str = "audio/wav"


class SpeechProcessResponse(BaseModel):
    session_id: str
    transcript: str
    mcp_context: dict[str, Any]
    agent_decision: LLMDecision | None = None
    gate_result: DecisionGatePayload | None = None
