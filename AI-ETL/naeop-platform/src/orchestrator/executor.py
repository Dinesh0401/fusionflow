"""Task execution engine for DAGs."""

import time
from typing import Any, Dict, Optional

from src.core.logger import get_logger
from src.orchestrator.dag_builder import DAGBuilder
from src.monitoring.metrics import Metrics
from src.monitoring.alerts import AlertManager


class Executor:
    def __init__(
        self,
        metrics: Optional[Metrics] = None,
        alert_manager: Optional[AlertManager] = None,
        max_retries: int = 1,
        retry_delay_seconds: float = 0.5,
        logger_name: str = __name__,
    ):
        self.task_status: Dict[str, str] = {}
        self.metrics = metrics or Metrics()
        self.alert_manager = alert_manager
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.logger = get_logger(logger_name)

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

        for task_name in order:
            task = dag_builder.tasks[task_name]
            self.metrics.start_timer(task_name)
            status = "completed"
            try:
                result = self._run_task(task_name, task.func, context)
                context[task_name] = result
                self.task_status[task_name] = "completed"
            except Exception as exc:  # pylint: disable=broad-except
                self.task_status[task_name] = "failed"
                status = "failed"
                if self.alert_manager:
                    self.alert_manager.trigger_alert(f"Task '{task_name}' failed: {exc}")
                raise
            finally:
                self.metrics.stop_timer(task_name, status=status)

        return context

    def get_task_status(self, task_id: str) -> str:
        return self.task_status.get(task_id, "not_started")