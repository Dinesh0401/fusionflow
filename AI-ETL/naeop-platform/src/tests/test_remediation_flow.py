import json

import pytest

from src.agents.contracts import AgentOutput, LLMRecommendedAction, LLMResponse
from src.agents.llm_agent import BaseAgent
from src.monitoring import llm_telemetry
from src.monitoring.metrics import Metrics
from src.monitoring.telemetry_schema import TelemetryStore
from src.orchestrator.dag_builder import DAGBuilder, Task
from src.orchestrator.decision_engine import DecisionEngine
from src.orchestrator.executor import Executor


class RetryAgent(BaseAgent):
    def generate_action_plan(self, context):
        response = LLMResponse(
            risk_summary="Failure detected",
            likely_root_cause=context.get("latest_error", "unknown"),
            confidence=0.95,
            recommended_action=LLMRecommendedAction(
                type="retry",
                parameters={"hint": "rerun"},
            ),
        )
        return AgentOutput(response=response, raw_text=json.dumps(response.to_dict()))


@pytest.mark.parametrize("threshold", [0.0])
def test_executor_retries_failed_task_with_remediation(tmp_path, monkeypatch, threshold):
    attempts = {"count": 0}

    def flaky_task(context):  # noqa: D401
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ValueError("synthetic failure")
        return ["ok"]

    dag = DAGBuilder(logger_name="RemediationDAG")
    dag.add_task(Task(name="flaky", func=flaky_task))

    telemetry_store = TelemetryStore(base_path=str(tmp_path), filename="telemetry.csv")
    metrics = Metrics()
    agent = RetryAgent()
    decision_engine = DecisionEngine(
        ml_risk_threshold=threshold,
        llm_confidence_threshold=0.5,
        human_in_loop=False,
    )

    temp_path = tmp_path / "llm_decisions.jsonl"
    monkeypatch.setattr(llm_telemetry, "_LLM_TELEMETRY_PATH", temp_path)

    executor = Executor(
        metrics=metrics,
        alert_manager=None,
        max_retries=0,
        telemetry_store=telemetry_store,
        pipeline_id="RetryPipeline",
        failure_predictor=None,
        automation_agent=agent,
        decision_engine=decision_engine,
    )

    result_context = executor.run(dag)

    assert attempts["count"] == 2
    assert executor.task_status["flaky"] == "completed"
    assert result_context["flaky"] == ["ok"]

    lines = temp_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    record = json.loads(lines[-1])
    assert record["decision"] == "execute"
    assert record["action_result"]["action"] == "retry"
    assert record["action_result"]["status"] == "succeeded"
