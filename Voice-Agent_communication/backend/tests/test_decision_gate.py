from app.schemas.llm import LLMDecision, RecommendedAction, RecommendedActionType
from app.services.decision_gate import DecisionGate, GateEvaluationInput, GateVerdict


def build_llm_decision(prompt_hash: str = "hash") -> LLMDecision:
    return LLMDecision(
        risk_summary="Okay",
        likely_root_cause="Test",
        confidence=0.9,
        recommended_action=RecommendedAction(type=RecommendedActionType.retry, parameters={}),
        provider="provider",
        model="model",
        prompt_hash=prompt_hash,
    )


def test_decision_gate_blocks_high_risk():
    gate = DecisionGate(ml_risk_threshold=0.5, llm_confidence_threshold=0.6)
    decision = gate.evaluate(
        GateEvaluationInput(
            ml_risk_score=0.8,
            llm_decision=build_llm_decision(),
            decision_type="retry",
            schema_valid=True,
        )
    )
    assert decision.verdict is GateVerdict.block
    assert decision.reason == "ml_risk_threshold_exceeded"


def test_decision_gate_blocks_low_confidence():
    gate = DecisionGate(ml_risk_threshold=0.9, llm_confidence_threshold=0.7)
    decision = gate.evaluate(
        GateEvaluationInput(
            ml_risk_score=0.2,
            llm_decision=build_llm_decision(),
            decision_type="retry",
            schema_valid=True,
        )
    )
    assert decision.verdict is GateVerdict.block
    assert decision.reason == "llm_confidence_below_threshold"


def test_decision_gate_blocks_missing_decision():
    gate = DecisionGate(ml_risk_threshold=0.9, llm_confidence_threshold=0.7)
    decision = gate.evaluate(
        GateEvaluationInput(
            ml_risk_score=0.2,
            llm_decision=None,
            decision_type=None,
            schema_valid=True,
        )
    )
    assert decision.verdict is GateVerdict.block
    assert decision.reason == "missing_llm_decision"


def test_decision_gate_allows_when_inputs_safe():
    gate = DecisionGate(ml_risk_threshold=0.9, llm_confidence_threshold=0.6)
    decision = gate.evaluate(
        GateEvaluationInput(
            ml_risk_score=0.1,
            llm_decision=build_llm_decision(),
            decision_type="retry",
            schema_valid=True,
        )
    )
    assert decision.verdict is GateVerdict.allow
*** End Patch