"""Task execution engine for DAGs."""

import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import uuid4

from src.core.logger import get_logger
from src.orchestrator.dag_builder import DAGBuilder
from src.monitoring.metrics import Metrics
from src.monitoring.alerts import AlertManager
from src.monitoring.telemetry_schema import TelemetryEvent, TelemetryStore

if TYPE_CHECKING:  # pragma: no cover
    from src.ml.failure_model import FailurePredictor


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
        failure_predictor: Optional["FailurePredictor"] = None,
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
                time.sleep(self.retry_delay_seconds)

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
            try:
                result = self._run_task(task_name, task.func, context)
                context[task_name] = result
                self.task_status[task_name] = "completed"
                rows_out = self._count_rows(result)
            except Exception as exc:  # pylint: disable=broad-except
                self.task_status[task_name] = "failed"
                status = "failed"
                if self.alert_manager:
                    self.alert_manager.trigger_alert(f"Task '{task_name}' failed: {exc}")
                rows_out = None
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

        if risk >= self.failure_predictor.risk_threshold:
            self.logger.warning("Predicted failure probability for pipeline '%s': %.2f", self.pipeline_id, risk)
            if self.alert_manager:
                self.alert_manager.trigger_alert(
                    f"Pipeline '{self.pipeline_id}' predicted failure risk {risk:.2f} exceeds threshold"
                )
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