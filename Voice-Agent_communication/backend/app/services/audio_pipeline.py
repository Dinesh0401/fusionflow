import logging
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError

from ..core.telemetry import get_tracer, record_gate_metrics
from ..schemas.decision import DecisionGatePayload
from ..schemas.llm import LLMDecision, compute_prompt_hash
from ..schemas.speech import SpeechProcessResponse
from .decision_gate import DecisionGate, GateEvaluationInput
from .mcp_context import MCPContextService
from .decision_ledger import DecisionLedger
from .telemetry import emit_gate_event


logger = logging.getLogger(__name__)

DEFAULT_PROMPT_TEMPLATE_ID = "vocaverse.conversation.v1"
DEFAULT_TOOLS_SCHEMA: dict[str, Any] = {
    "version": "2025-12-01",
    "tools": [
        {"name": "grammar_check"},
        {"name": "fluency_score"},
        {"name": "vocabulary_suggestion"},
    ],
}
MCP_CONTRACT_VERSION = "v1"


class AudioPipelineService:
    """Coordinates speech-to-text, MCP updates, and agent responses."""

    def __init__(self, settings, decision_ledger: DecisionLedger | None = None) -> None:
        self._settings = settings
        self._context_service = MCPContextService(base_url=settings.mcp_server_url, api_key=settings.mcp_api_key)
        self._decision_gate = DecisionGate(
            ml_risk_threshold=settings.ml_risk_threshold,
            llm_confidence_threshold=settings.llm_confidence_threshold,
            blocked_providers=settings.blocked_providers,
            blocked_models=settings.blocked_models,
        )
        self._ledger = decision_ledger
        self._tracer = get_tracer()

    async def process_audio(self, session_id: str, audio_bytes: bytes) -> SpeechProcessResponse:
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio payload")

        # TODO: integrate actual STT provider
        transcript = self._fake_transcribe(audio_bytes)

        rendered_prompt = self._render_prompt(transcript)
        prompt_hash = compute_prompt_hash(
            prompt_template_id=DEFAULT_PROMPT_TEMPLATE_ID,
            prompt=rendered_prompt,
            tools_schema=DEFAULT_TOOLS_SCHEMA,
            contract_version=MCP_CONTRACT_VERSION,
        )

        turn_payload: dict[str, Any] = {
            "speaker": "user",
            "transcript": transcript,
            "metadata": {
                "prompt_template_id": DEFAULT_PROMPT_TEMPLATE_ID,
                "prompt_hash": prompt_hash,
                "contract_version": MCP_CONTRACT_VERSION,
                "tools_schema_version": DEFAULT_TOOLS_SCHEMA["version"],
            },
        }
        with self._tracer.start_as_current_span("mcp.push_turn") as span:
            span.set_attribute("session_id", session_id)
            span.set_attribute("prompt_hash", prompt_hash)
            span.set_attribute("prompt_template_id", DEFAULT_PROMPT_TEMPLATE_ID)
            mcp_response = await self._context_service.push_turn(session_id=session_id, turn=turn_payload)

        agent_response_raw = mcp_response.get("agent_response")
        agent_response: LLMDecision | None = None
        schema_valid = True
        if agent_response_raw is not None:
            try:
                agent_response = LLMDecision.model_validate(agent_response_raw)
            except ValidationError as exc:
                schema_valid = False
                logger.warning("Invalid LLM decision payload received", exc_info=exc)
        else:
            schema_valid = False

        ml_risk_score = self._extract_ml_risk_score(mcp_response)
        gate_input = GateEvaluationInput(
            ml_risk_score=ml_risk_score,
            llm_decision=agent_response,
            decision_type=agent_response.recommended_action.type if agent_response else None,
            schema_valid=schema_valid,
        )
        with self._tracer.start_as_current_span("decision_gate") as gate_span:
            gate_span.set_attribute("ml_risk_score", ml_risk_score)
            gate_span.set_attribute("prompt_hash", prompt_hash)
            gate_span.set_attribute("schema_valid", schema_valid)
            if agent_response:
                gate_span.set_attribute("provider", agent_response.provider)
                gate_span.set_attribute("model", agent_response.model)
                gate_span.set_attribute("llm_confidence", agent_response.confidence)
            gate_result = self._decision_gate.evaluate(gate_input)
            gate_span.set_attribute("verdict", gate_result.verdict.value)
            gate_span.set_attribute("reason", gate_result.reason)

        gate_payload = DecisionGatePayload(
            verdict=gate_result.verdict,
            reason=gate_result.reason,
            ml_risk_score=ml_risk_score,
            llm_confidence=agent_response.confidence if agent_response else None,
            decision_type=agent_response.recommended_action.type if agent_response else None,
            provider=agent_response.provider if agent_response else None,
            model=agent_response.model if agent_response else None,
            schema_valid=schema_valid,
            prompt_hash=agent_response.prompt_hash if agent_response else prompt_hash,
        )

        context_snapshot = mcp_response.get("context", {})

        response = SpeechProcessResponse(
            session_id=session_id,
            transcript=transcript,
            mcp_context=context_snapshot,
            agent_decision=agent_response,
            gate_result=gate_payload,
        )

        if self._ledger:
            try:
                record = await self._ledger.record_event(gate_payload, agent_response)
            except Exception:
                logger.exception("Failed to persist decision ledger event")
            else:
                record_gate_metrics(record)
                try:
                    await emit_gate_event(record)
                except Exception:
                    logger.exception("Failed to emit gate telemetry")

        return response

    @staticmethod
    def _fake_transcribe(_audio: bytes) -> str:
        # Stub that will later call a speech-to-text service
        return "[stub transcript]"

    @staticmethod
    def _extract_ml_risk_score(mcp_response: dict[str, Any]) -> float:
        metrics = mcp_response.get("metrics", {})
        try:
            raw_value = float(metrics.get("ml_risk_score", 0.0))
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, raw_value))

    @staticmethod
    def _render_prompt(transcript: str) -> str:
        cleaned = transcript.strip()
        return (
            "Assess the following English utterance for fluency, correctness, and vocabulary opportunities:"  # noqa: E501
            f"\n\n{cleaned}"
        )
