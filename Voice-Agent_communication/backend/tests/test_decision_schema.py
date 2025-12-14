import pytest
from pydantic import ValidationError

from app.schemas.decision import DecisionGatePayload, DecisionVerdict


def test_gate_payload_enforces_risk_bounds():
    with pytest.raises(ValidationError):
        DecisionGatePayload(
            verdict=DecisionVerdict.allow,
            reason="ok",
            ml_risk_score=1.5,
        )


def test_gate_payload_enforces_confidence_bounds():
    with pytest.raises(ValidationError):
        DecisionGatePayload(
            verdict=DecisionVerdict.allow,
            reason="ok",
            ml_risk_score=0.2,
            llm_confidence=-0.1,
        )


def test_gate_payload_forbids_extra_fields():
    with pytest.raises(ValidationError):
        DecisionGatePayload(
            verdict=DecisionVerdict.allow,
            reason="ok",
            ml_risk_score=0.1,
            unknown="value",  # type: ignore[arg-type]
        )


def test_gate_payload_accepts_prompt_hash():
    payload = DecisionGatePayload(
        verdict=DecisionVerdict.block,
        reason="schema_invalid",
        ml_risk_score=0.5,
        schema_valid=False,
        prompt_hash="legacy",
    )
    assert payload.prompt_hash == "legacy"
*** End Patch