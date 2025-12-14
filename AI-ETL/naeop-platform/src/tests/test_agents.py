import tempfile

import pytest

from src.agents.contracts import AgentOutput
from src.agents.llm_agent import AgentConfig, LLMAgent, MockAgent
from src.monitoring.metrics import Metrics
from src.monitoring.telemetry_schema import TelemetryStore
from src.orchestrator.dag_builder import DAGBuilder, Task
from src.orchestrator.executor import Executor


def test_mock_agent_returns_deterministic_plan():
    agent = MockAgent()
    output = agent.generate_action_plan(
        {
            "pipeline_id": "Pipeline-A",
            "predicted_risk": 0.91,
            "failed_tasks": ["transform"],
            "latest_error": "Timeout",
        }
    )

    assert isinstance(output, AgentOutput)
    assert "Pipeline-A" in output.response.risk_summary
    assert output.response.likely_root_cause == "Timeout"
    assert output.response.confidence == 0.5


def test_llm_agent_without_provider_falls_back(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = AgentConfig(enabled=True, provider="openai")
    agent = LLMAgent(config=config)

    output = agent.generate_action_plan(
        {
            "pipeline_id": "Pipeline-B",
            "predicted_risk": 0.75,
        }
    )

    assert isinstance(output, AgentOutput)
    assert "Pipeline-B" in output.response.risk_summary


def test_executor_invokes_automation_agent_on_failure(tmp_path):
    class RecordingAgent(MockAgent):
        def __init__(self):
            self.invocations = []

        def generate_action_plan(self, context):
            self.invocations.append(context)
            return super().generate_action_plan(context)

    dag = DAGBuilder(logger_name="TestExecutorAgent")

    def fail_task(context):  # noqa: D401
        raise ValueError("synthetic failure")

    dag.add_task(Task(name="fail", func=fail_task))

    telemetry_store = TelemetryStore(base_path=str(tmp_path), filename="telemetry.csv")
    agent = RecordingAgent()

    executor = Executor(
        metrics=Metrics(),
        alert_manager=None,
        telemetry_store=telemetry_store,
        pipeline_id="AgentPipeline",
        failure_predictor=None,
        automation_agent=agent,
    )

    executor.run(dag)

    assert agent.invocations
    context = agent.invocations[-1]
    assert context["pipeline_id"] == "AgentPipeline"
    assert context.get("latest_error") == "synthetic failure"
    assert "fail" in context.get("failed_tasks", [])
    assert executor.task_status["fail"] == "completed"
