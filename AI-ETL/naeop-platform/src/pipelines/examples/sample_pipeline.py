"""Example ETL pipeline demonstrating DAG orchestration."""

from typing import Any, Dict, List

from src.adapters.transformations.transformer import DataTransformer
from src.config.settings import get_settings
from src.core.logger import get_logger
from src.orchestrator.dag_builder import DAGBuilder, Task
from src.orchestrator.executor import Executor
from src.ml.failure_model import FailurePredictor
from src.monitoring.alerts import AlertManager
from src.monitoring.metrics import Metrics


class SamplePipeline:
    """Minimal yet realistic ETL pipeline used for examples and tests."""

    def __init__(self):
        self.name = "Sample Pipeline"
        self.status = "initialized"
        self.output: List[Dict[str, Any]] = []
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__, level=self.settings.log_level)

        self.metrics = Metrics()
        self.alerts = AlertManager(threshold=5.0)
        self.builder = DAGBuilder(logger_name=self.__class__.__name__)
        self.failure_predictor = FailurePredictor(
            telemetry_path=self.settings.telemetry_path,
            model_path=self.settings.failure_model_path,
            risk_threshold=self.settings.failure_risk_threshold,
        )
        self._build_graph()

    def _build_graph(self) -> None:
        self.builder.add_task(Task(name="extract", func=self._extract))
        self.builder.add_task(Task(name="transform", func=self._transform))
        self.builder.add_task(Task(name="load", func=self._load))

        self.builder.add_dependency("transform", "extract")
        self.builder.add_dependency("load", "transform")

    def _extract(self, context):
        """Simulate data extraction. In production, call an adapter."""

        data = [
            {"id": 1, "value": 10},
            {"id": 2, "value": 20},
            {"id": 3, "value": 30},
        ]
        self.logger.info("Extracted %s records", len(data))
        return data

    def _transform(self, context):
        raw = context.get("extract", [])
        transformer = DataTransformer()
        transformed = transformer.transform(raw)
        self.logger.info("Transformed dataset to %s rows", len(transformed))
        return transformed

    def _load(self, context):
        transformed = context.get("transform", [])
        # Persist in-memory for demonstration; a real implementation would call the warehouse adapter.
        self.output = transformed if isinstance(transformed, list) else transformed.to_dict(orient="records")
        self.logger.info("Loaded %s records", len(self.output))
        return True

    def execute(self) -> bool:
        self.status = "running"
        executor = Executor(
            metrics=self.metrics,
            alert_manager=self.alerts,
            max_retries=self.settings.max_retries,
            retry_delay_seconds=self.settings.retry_delay_seconds,
            logger_name=self.__class__.__name__,
            pipeline_id=self.name,
            telemetry_store=None,
            failure_predictor=self.failure_predictor,
        )

        try:
            executor.run(self.builder, initial_context={})
            self.status = "completed"
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self.status = "failed"
            self.logger.error("Pipeline execution failed: %s", exc)
            return False

    def get_output(self):
        return self.output


def run_pipeline():
    pipeline = SamplePipeline()
    pipeline.execute()


if __name__ == "__main__":
    run_pipeline()