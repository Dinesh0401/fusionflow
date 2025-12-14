"""Example ETL pipeline demonstrating DAG orchestration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agents.llm_agent import AgentConfig, BaseAgent, LLMAgent, MockAgent
from src.adapters.transformations.transformer import DataTransformer
from src.config.settings import get_settings
from src.core.logger import get_logger
from src.orchestrator.dag_builder import DAGBuilder, Task
from src.orchestrator.executor import Executor
from src.orchestrator.decision_engine import DecisionEngine
from src.ml.failure_model import FailurePredictor

try:  # pragma: no cover - advanced predictor is optional at runtime
    from src.ml.advanced_failure_model import AdvancedFailurePredictor
except ImportError:  # pragma: no cover
    AdvancedFailurePredictor = None  # type: ignore
from src.monitoring.alerts import AlertManager
from src.monitoring.metrics import Metrics
from src.monitoring.telemetry_schema import TelemetryStore


class SamplePipeline:
    """Minimal yet realistic ETL pipeline used for examples and tests."""

    def __init__(
        self,
        telemetry_store: Optional[TelemetryStore] = None,
        automation_agent: Optional[BaseAgent] = None,
    ):
        self.name = "Sample Pipeline"
        self.status = "initialized"
        self.output: List[Dict[str, Any]] = []
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__, level=self.settings.log_level)

        self.metrics = Metrics()
        self.alerts = AlertManager(threshold=5.0)
        self.builder = DAGBuilder(logger_name=self.__class__.__name__)
        self.telemetry_store = telemetry_store or self._default_telemetry_store()
        self.automation_agent = automation_agent or self._build_automation_agent()
        self.decision_engine = DecisionEngine(
            ml_risk_threshold=self.settings.failure_risk_threshold,
            llm_confidence_threshold=self.settings.llm_agent_decision_threshold,
            human_in_loop=self.settings.llm_agent_human_in_loop,
        )
        baseline_predictor = FailurePredictor(
            telemetry_path=self.settings.telemetry_path,
            model_path=self.settings.failure_model_path,
            risk_threshold=self.settings.failure_risk_threshold,
        )
        self.failure_predictor = baseline_predictor

        if self.settings.use_advanced_failure_model and AdvancedFailurePredictor is not None:
            try:
                self.failure_predictor = AdvancedFailurePredictor(
                    telemetry_path=self.settings.telemetry_path,
                    model_path=self.settings.advanced_failure_model_path,
                    risk_threshold=self.settings.failure_risk_threshold,
                    baseline_predictor=baseline_predictor,
                    ensemble_weight=self.settings.failure_risk_ensemble_weight,
                )
            except Exception as exc:  # pragma: no cover - fall back gracefully
                self.logger.warning("Advanced failure predictor unavailable; falling back to baseline: %s", exc)
                self.failure_predictor = baseline_predictor
        self._build_graph()

    def _default_telemetry_store(self) -> TelemetryStore:
        telemetry_path = Path(self.settings.telemetry_path)
        return TelemetryStore(base_path=str(telemetry_path.parent), filename=telemetry_path.name)

    def _build_automation_agent(self) -> BaseAgent:
        config = AgentConfig(
            enabled=self.settings.llm_agent_enabled,
            provider=self.settings.llm_agent_provider,
            model=self.settings.llm_agent_model,
            temperature=self.settings.llm_agent_temperature,
            max_output_tokens=self.settings.llm_agent_max_tokens,
            api_key_env=self.settings.llm_agent_api_key_env,
            endpoint=self.settings.llm_agent_endpoint or None,
        )
        if not config.enabled:
            return MockAgent()
        if config.provider.lower() == "mock":
            return MockAgent()
        return LLMAgent(config=config, fallback=MockAgent())

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
            telemetry_store=self.telemetry_store,
            failure_predictor=self.failure_predictor,
            automation_agent=self.automation_agent,
            decision_engine=self.decision_engine,
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