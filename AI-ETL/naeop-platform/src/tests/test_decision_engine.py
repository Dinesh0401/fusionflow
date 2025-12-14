import json

from src.agents.contracts import AgentOutput, LLMRecommendedAction, LLMResponse
from src.monitoring import llm_telemetry
from src.monitoring.llm_telemetry import log_llm_decision
from src.orchestrator.decision_engine import DecisionEngine


def _sample_output(confidence: float) -> AgentOutput:
    response = LLMResponse(
        risk_summary="Risk extremely high",
        likely_root_cause="SyntheticFailure",
        confidence=confidence,
        recommended_action=LLMRecommendedAction(type="retry", parameters={"attempts": "1"}),
    )
    return AgentOutput(response=response, raw_text=json.dumps(response.to_dict()))


def test_decision_engine_requests_human_when_low_confidence():
    engine = DecisionEngine(ml_risk_threshold=0.6, llm_confidence_threshold=0.7, human_in_loop=True)
    output = _sample_output(confidence=0.4)

    result = engine.decide(ml_failure_risk=0.95, llm_response=output.response)

    assert result.verdict == "request_human"
    assert result.ml_risk == 0.95


def test_decision_engine_executes_when_confident():
    engine = DecisionEngine(ml_risk_threshold=0.6, llm_confidence_threshold=0.7, human_in_loop=True)
    output = _sample_output(confidence=0.9)

    result = engine.decide(ml_failure_risk=0.92, llm_response=output.response)

    assert result.verdict == "execute"
    assert result.llm_response == output.response


def test_log_llm_decision_persists_record(tmp_path, monkeypatch):
    temp_path = tmp_path / "llm_decisions.jsonl"
    monkeypatch.setattr(llm_telemetry, "_LLM_TELEMETRY_PATH", temp_path)

    output = _sample_output(confidence=0.8)
    log_llm_decision(
        pipeline_id="Pipeline-Z",
        provider="mock",
        model="deterministic",
        context={"foo": "bar"},
        agent_output=output,
        decision="execute",
    )

    lines = temp_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    payload = json.loads(lines[-1])
    assert payload["pipeline_id"] == "Pipeline-Z"
    assert payload["decision"] == "execute"
    assert payload["response"]["confidence"] == 0.8
    assert payload["action_result"] == {}
