"""Task execution engine for DAGs."""

import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol
from uuid import uuid4

from src.agents.contracts import AgentOutput
from src.agents.llm_agent import BaseAgent
from src.monitoring.metrics import Metrics
from src.monitoring.alerts import AlertManager
from src.monitoring.alert_contracts import AlertPayload
from src.monitoring.alert_backends import AlertBackend, StdoutAlertBackend
from src.monitoring.telemetry_schema import TelemetryEvent, TelemetryStore
from src.monitoring.llm_telemetry import log_llm_decision
from src.core.logger import get_logger
from src.orchestrator.dag_builder import DAGBuilder
from src.orchestrator.decision_engine import DecisionEngine, DecisionResult
from src.orchestrator.remediation import RemediationExecutor
from src.orchestrator.retry_policy import RetryPolicy, FixedRetryPolicy

if TYPE_CHECKING:  # pragma: no cover

    class FailureRiskScorer(Protocol):
        risk_threshold: float

        def predict_pipeline_risk(self, pipeline_id: str) -> Optional[float]:
            ...


class Executor:
    def __init__(
        self,
        metrics: Optional[Metrics] = None,
        alert_manager: Optional[AlertManager] = None,
        max_retries: int = 1,
        retry_delay_seconds: float = 0.5,
        logger_name: str = __name__,
        pipeline_id: str = "default",
        run_id: Optional[str] = None,
        telemetry_store: Optional[TelemetryStore] = None,
        failure_predictor: Optional["FailureRiskScorer"] = None,
        automation_agent: Optional[BaseAgent] = None,
        decision_engine: Optional[DecisionEngine] = None,
        remediation_executor: Optional[RemediationExecutor] = None,
        retry_policy: Optional[RetryPolicy] = None,
        alert_backend: Optional[AlertBackend] = None,
    ):
        self.task_status: Dict[str, str] = {}
        self.metrics = metrics or Metrics()
        self.alert_manager = alert_manager
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.logger = get_logger(logger_name)
        self.pipeline_id = pipeline_id
        self.run_id = run_id or str(uuid4())
        self.telemetry_store = telemetry_store or TelemetryStore()
        self.failure_predictor = failure_predictor
        self.automation_agent = automation_agent
        self._latest_risk: Optional[float] = None
        self.decision_engine = decision_engine
        self.remediation_executor = remediation_executor or RemediationExecutor(self)
        self._latest_agent_output: Optional[AgentOutput] = None
        self._latest_decision: Optional[DecisionResult] = None
        self.retry_policy: RetryPolicy = retry_policy or FixedRetryPolicy(delay_seconds=retry_delay_seconds)
        self.alert_backend: AlertBackend = alert_backend or StdoutAlertBackend()

    def _run_task(self, task_name: str, task_callable, context: Dict[str, Any]) -> Any:
        attempts = 0
        while attempts <= self.max_retries:
            try:
                self.logger.info("Running task '%s' (attempt %s)", task_name, attempts + 1)
                return task_callable(context)
            except Exception as exc:  # pylint: disable=broad-except
                attempts += 1
                self.logger.error("Task '%s' failed: %s", task_name, exc)
                if attempts > self.max_retries:
                    raise
                delay = self.retry_policy.delay(attempts)
                self.logger.info("Retrying task '%s' after %.2fs delay", task_name, delay)
                time.sleep(delay)

    def run(self, dag_builder: DAGBuilder, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context: Dict[str, Any] = initial_context or {}
        order = dag_builder.get_execution_order()

        self._emit_risk_prediction()

        for task_name in order:
            task = dag_builder.tasks[task_name]
            start_ts = datetime.utcnow()
            rows_in = self._count_rows(self._get_dependency_result(task_name, dag_builder, context))
            self.metrics.start_timer(task_name)
            status = "completed"
            rows_out: Optional[int] = None
            handled = False
            action_result: Optional[Dict[str, Any]] = None
            decision: Optional[DecisionResult] = None
            try:
                result = self._run_task(task_name, task.func, context)
                context[task_name] = result
                self.task_status[task_name] = "completed"
                rows_out = self._count_rows(result)
            except Exception as exc:  # pylint: disable=broad-except
                self.task_status[task_name] = "failed"
                status = "failed"
                self._send_alert(
                    severity="ERROR",
                    title=f"Task '{task_name}' failed",
                    message=str(exc),
                    action="none",
                )
                if self.alert_manager:
                    self.alert_manager.trigger_alert(f"Task '{task_name}' failed: {exc}")
                agent_context = self._build_agent_context(
                    {
                        "latest_error": str(exc),
                        "failed_tasks": [task_name],
                    }
                )
                decision = self._invoke_agent(agent_context, auto_publish=False)
                if (
                    decision
                    and self.remediation_executor
                    and self._latest_agent_output is not None
                ):
                    action_result = self.remediation_executor.execute(
                        decision=decision,
                        agent_output=self._latest_agent_output,
                        context=context,
                        task_name=task_name,
                        dag_builder=dag_builder,
                    )
                    if action_result.get("status") == "succeeded":
                        handled = True
                        status = "completed"
                        result = context.get(task_name)
                        rows_out = self._count_rows(result)
                        self.task_status[task_name] = "completed"
                if decision and self._latest_agent_output is not None:
                    self._publish_agent_result(decision, self._latest_agent_output, agent_context, action_result)
                if not handled:
                    raise
            finally:
                self.metrics.stop_timer(task_name, status=status)
                end_ts = datetime.utcnow()
                duration_ms = (end_ts - start_ts).total_seconds() * 1000
                event = TelemetryEvent(
                    pipeline_id=self.pipeline_id,
                    run_id=self.run_id,
                    task_id=task_name,
                    step=task_name,
                    status=status,
                    start_time=start_ts,
                    end_time=end_ts,
                    duration_ms=duration_ms,
                    rows_in=rows_in,
                    rows_out=rows_out,
                    error_type=None if status == "completed" else "TaskError",
                    resource_cpu=None,
                    resource_mem=None,
                )
                self.telemetry_store.add_event(event)

        self.telemetry_store.flush()
        return context

    def get_task_status(self, task_id: str) -> str:
        return self.task_status.get(task_id, "not_started")

    def _emit_risk_prediction(self) -> None:
        if not self.failure_predictor:
            return
        try:
            risk = self.failure_predictor.predict_pipeline_risk(self.pipeline_id)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failure predictor unavailable: %s", exc)
            return

        if risk is None:
            return

        self._latest_risk = risk
        if risk >= self.failure_predictor.risk_threshold:
            self.logger.warning("Predicted failure probability for pipeline '%s': %.2f", self.pipeline_id, risk)
            if self.alert_manager:
                self.alert_manager.trigger_alert(
                    f"Pipeline '{self.pipeline_id}' predicted failure risk {risk:.2f} exceeds threshold"
                )
            self._invoke_agent(self._build_agent_context({"predicted_risk": risk}))
        else:
            self.logger.info(
                "Predicted failure probability for pipeline '%s': %.2f (below threshold)",
                self.pipeline_id,
                risk,
            )

    @staticmethod
    def _count_rows(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            if hasattr(value, "shape") and len(getattr(value, "shape")) > 0:
                return int(value.shape[0])
            if isinstance(value, (list, tuple, set)):
                return len(value)
        except Exception:  # noqa: BLE001
            return None
        return None

    @staticmethod
    def _get_dependency_result(task_name: str, dag_builder: DAGBuilder, context: Dict[str, Any]) -> Any:
        deps = dag_builder.dependencies.get(task_name, [])
        if not deps:
            return None
        # Use the first dependency's output as proxy for rows_in
        first_dep = deps[0]
        return context.get(first_dep)

    def _build_agent_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        failed_tasks = [task for task, status in self.task_status.items() if status == "failed"]
        summary = [f"{task}: {status}" for task, status in self.task_status.items()]
        base = {
            "pipeline_id": self.pipeline_id,
            "run_id": self.run_id,
            "predicted_risk": self._latest_risk,
            "failed_tasks": failed_tasks,
            "telemetry_summary": summary,
        }
        base.update(extra)
        return base

    def _invoke_agent(self, context: Dict[str, Any], auto_publish: bool = True) -> Optional[DecisionResult]:
        if not self.automation_agent:
            return None

        try:
            agent_output = self.automation_agent.generate_action_plan(context)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Automation agent invocation failed: %s", exc)
            return None

        if not isinstance(agent_output, AgentOutput):
            self.logger.error("Automation agent returned unexpected payload: %s", type(agent_output))
            return None

        self._latest_agent_output = agent_output
        decision = self._apply_decision_policy(agent_output, context)
        self._latest_decision = decision

        if auto_publish:
            self._publish_agent_result(decision, agent_output, context, action_result=None)

        return decision

    def _apply_decision_policy(self, agent_output: AgentOutput, context: Dict[str, Any]) -> DecisionResult:
        if self.decision_engine:
            risk_value = context.get("predicted_risk", self._latest_risk)
            return self.decision_engine.decide(risk_value, agent_output.response)
        return DecisionResult(
            verdict="execute",
            ml_risk=float(self._latest_risk or 0.0),
            llm_response=agent_output.response,
        )

    @staticmethod
    def _render_plan(agent_output: AgentOutput) -> str:
        response = agent_output.response
        action = response.recommended_action
        parameters = ", ".join(f"{key}={value}" for key, value in action.parameters.items()) or "none"
        return (
            f"Risk Summary: {response.risk_summary}\n"
            f"Likely Root Cause: {response.likely_root_cause}\n"
            f"Recommended Action: {action.type} ({parameters})"
        )

    def _publish_agent_result(
        self,
        decision: DecisionResult,
        agent_output: AgentOutput,
        context: Dict[str, Any],
        action_result: Optional[Dict[str, Any]],
    ) -> None:
        plan_text = self._render_plan(agent_output)
        action_suffix = ""
        if action_result:
            action_suffix = (
                f" | action={action_result.get('action')}"
                f" ({action_result.get('status')})"
            )
            detail = action_result.get("detail")
            if detail:
                action_suffix += f" - {detail}"

        message = (
            f"Automation agent decision for pipeline '{self.pipeline_id}' "
            f"[{decision.verdict} | confidence={agent_output.response.confidence:.2f}]:\n"
            f"{plan_text}{action_suffix}"
        )
        self.logger.info(message)
        if self.alert_manager:
            self.alert_manager.trigger_alert(message)

        provider = getattr(self.automation_agent, "provider", "unknown") or "unknown"
        config = getattr(self.automation_agent, "config", None)
        model = getattr(config, "model", "n/a") if config else "n/a"
        log_llm_decision(
            pipeline_id=self.pipeline_id,
            provider=str(provider),
            model=str(model),
            context=context,
            agent_output=agent_output,
            decision=decision.verdict,
            action_result=action_result,
        )

    def _retry_task(self, task_name: str, task_callable, context: Dict[str, Any]):
        try:
            result = self._run_task(task_name, task_callable, context)
            return True, result, None
        except Exception as exc:  # noqa: BLE001
            return False, None, exc

    def _send_alert(
        self,
        severity: str,
        title: str,
        message: str,
        action: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Route an alert through the configured alert backend."""
        payload = AlertPayload(
            pipeline_id=self.pipeline_id,
            run_id=self.run_id,
            severity=severity,
            title=title,
            message=message,
            action=action,
            metadata=metadata or {},
        )
        return self.alert_backend.send(payload)