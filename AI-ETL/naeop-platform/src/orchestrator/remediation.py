"""Execute remediation actions recommended by the automation agent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from src.agents.contracts import AgentOutput
from src.orchestrator.decision_engine import DecisionResult

if TYPE_CHECKING:  # pragma: no cover
    from src.orchestrator.executor import Executor
    from src.orchestrator.dag_builder import DAGBuilder, Task


class RemediationExecutor:
    """Map high-level agent directives to concrete remediation actions."""

    def __init__(self, executor: "Executor") -> None:
        self.executor = executor

    def execute(
        self,
        *,
        decision: DecisionResult,
        agent_output: AgentOutput,
        context: Dict[str, Any],
        task_name: Optional[str] = None,
        dag_builder: Optional["DAGBuilder"] = None,
    ) -> Dict[str, Any]:
        action_type = agent_output.response.recommended_action.type or "none"
        result: Dict[str, Any] = {
            "action": action_type,
            "status": "skipped",
            "detail": "",
        }

        if decision.verdict != "execute":
            result["detail"] = f"Decision verdict '{decision.verdict}' prevents automation"
            return result

        handler = getattr(self, f"_handle_{action_type}", None)
        if not callable(handler):
            result["detail"] = "No remediation handler available"
            return result

        return handler(
            context=context,
            task_name=task_name,
            dag_builder=dag_builder,
            agent_output=agent_output,
        )

    # Handlers -----------------------------------------------------------------

    def _handle_retry(
        self,
        *,
        context: Dict[str, Any],
        task_name: Optional[str],
        dag_builder: Optional["DAGBuilder"],
        agent_output: AgentOutput,
    ) -> Dict[str, Any]:
        if not task_name or not dag_builder:
            return {
                "action": "retry",
                "status": "failed",
                "detail": "Missing task context for retry",
            }
        task = dag_builder.tasks.get(task_name)
        if task is None:
            return {
                "action": "retry",
                "status": "failed",
                "detail": f"Task '{task_name}' not found",
            }

        success, output, error = self.executor._retry_task(task_name, task.func, context)
        if success:
            context[task_name] = output
            return {
                "action": "retry",
                "status": "succeeded",
                "detail": "Retry completed successfully",
            }
        return {
            "action": "retry",
            "status": "failed",
            "detail": str(error) if error else "Retry failed",
        }

    def _handle_skip(
        self,
        *,
        context: Dict[str, Any],
        task_name: Optional[str],
        dag_builder: Optional["DAGBuilder"],
        agent_output: AgentOutput,
    ) -> Dict[str, Any]:
        if not task_name:
            return {
                "action": "skip",
                "status": "failed",
                "detail": "No task provided to skip",
            }
        self.executor.task_status[task_name] = "skipped"
        context[task_name] = None
        return {
            "action": "skip",
            "status": "succeeded",
            "detail": "Task marked as skipped by remediation",
        }

    def _handle_alert(
        self,
        *,
        context: Dict[str, Any],
        task_name: Optional[str],
        dag_builder: Optional["DAGBuilder"],
        agent_output: AgentOutput,
    ) -> Dict[str, Any]:
        if self.executor.alert_manager:
            message = agent_output.raw_text or agent_output.response.risk_summary
            self.executor.alert_manager.trigger_alert(
                f"Remediation alert for {self.executor.pipeline_id}: {message}"
            )
        return {
            "action": "alert",
            "status": "succeeded",
            "detail": "Alert emitted",
        }

    def _handle_none(
        self,
        *,
        context: Dict[str, Any],
        task_name: Optional[str],
        dag_builder: Optional["DAGBuilder"],
        agent_output: AgentOutput,
    ) -> Dict[str, Any]:
        return {
            "action": "none",
            "status": "skipped",
            "detail": "Agent indicated no remediation required",
        }

    def _handle_tune(
        self,
        *,
        context: Dict[str, Any],
        task_name: Optional[str],
        dag_builder: Optional["DAGBuilder"],
        agent_output: AgentOutput,
    ) -> Dict[str, Any]:
        return {
            "action": "tune",
            "status": "skipped",
            "detail": "Tuning not automated; manual follow-up required",
        }
