import math

import pytest
from pydantic import ValidationError

from app.schemas.llm import (
    LLMDecision,
    RecommendedAction,
    RecommendedActionType,
    compute_prompt_hash,
)


@pytest.fixture
def base_decision_payload():
    return {
        "risk_summary": "High pause frequency detected",
        "likely_root_cause": "User hesitated before responding",
        "confidence": 0.75,
        "recommended_action": {
            "type": RecommendedActionType.retry.value,
            "parameters": {"delay_seconds": 5},
        },
        "provider": "test-provider",
        "model": "test-model",
        "prompt_hash": "abc123",
    }


def test_llm_decision_rejects_confidence_out_of_bounds(base_decision_payload):
    payload = base_decision_payload.copy()
    payload["confidence"] = 1.2
    with pytest.raises(ValidationError):
        LLMDecision.model_validate(payload)


def test_llm_decision_rejects_negative_confidence(base_decision_payload):
    payload = base_decision_payload.copy()
    payload["confidence"] = -0.01
    with pytest.raises(ValidationError):
        LLMDecision.model_validate(payload)


def test_llm_decision_forbids_extra_fields(base_decision_payload):
    payload = base_decision_payload.copy()
    payload["unexpected"] = "value"
    with pytest.raises(ValidationError):
        LLMDecision.model_validate(payload)


def test_compute_prompt_hash_deterministic():
    schema = {"version": "1.0", "tools": [{"name": "grammar_check"}]}
    hash_one = compute_prompt_hash(
        prompt_template_id="template.v1",
        prompt="   Evaluate phrase   ",
        tools_schema=schema,
        contract_version="v1",
    )
    hash_two = compute_prompt_hash(
        prompt_template_id="template.v1",
        prompt="Evaluate phrase",
        tools_schema={"tools": [{"name": "grammar_check"}], "version": "1.0"},
        contract_version="v1",
    )
    assert hash_one == hash_two


def test_compute_prompt_hash_differs_for_schema_change():
    base_schema = {"version": "1.0", "tools": []}
    hash_one = compute_prompt_hash(
        prompt_template_id="template.v1",
        prompt="Assess",
        tools_schema=base_schema,
        contract_version="v1",
    )
    modified_schema = {"version": "1.1", "tools": []}
    hash_two = compute_prompt_hash(
        prompt_template_id="template.v1",
        prompt="Assess",
        tools_schema=modified_schema,
        contract_version="v1",
    )
    assert hash_one != hash_two


def test_recommended_action_serialization(base_decision_payload):
    decision = LLMDecision.model_validate(base_decision_payload)
    assert isinstance(decision.recommended_action, RecommendedAction)
    assert decision.recommended_action.type is RecommendedActionType.retry
*** End Patch