"""MLflow autologger for FusionFlow.

Opt-in via ``pip install fusionflow[mlflow]``. Logs:
- params: model.type_name, model.params, IR version, experiment name, seed
- metrics: every key from RunResult.metrics
- artifacts: the RunResult JSON itself (run.json)

Usage:
    >>> from fusionflow.integrations.mlflow_logger import log_run_result
    >>> log_run_result(plan, result, run_name="my_run")

If mlflow is not installed, raises MLflowNotInstalledError with a clear message.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fusionflow.executor.plan import ExecutionPlan
from fusionflow.executor.run_result import RunResult, RunStatus


class MLflowNotInstalledError(RuntimeError):
    """Raised when MLflow is requested but not installed."""


def _import_mlflow():
    """Import mlflow lazily. Raises MLflowNotInstalledError with install hint."""
    try:
        import mlflow  # type: ignore
        return mlflow
    except ImportError as exc:
        raise MLflowNotInstalledError(
            "MLflow is not installed. Install with: pip install fusionflow[mlflow]"
        ) from exc


def _ir_hash(payload: Dict[str, Any]) -> str:
    """SHA-256 of the canonical JSON IR. Useful as a content-addressable plan ID."""
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def log_run_result(
    plan: ExecutionPlan,
    result: RunResult,
    run_name: Optional[str] = None,
    experiment_name: Optional[str] = None,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Log an executed run to MLflow.

    Args:
        plan: The ExecutionPlan that was executed (used for params + IR hash).
        result: The RunResult produced by the backend.
        run_name: Optional explicit run name. Defaults to ``plan.experiment_name``.
        experiment_name: Optional MLflow experiment name. Defaults to "fusionflow".
        extra_params: Optional dict of extra params to log (e.g., {"seed": 42}).

    Returns:
        The MLflow run_id (str), or None if the result was SKIPPED.

    Raises:
        MLflowNotInstalledError: if mlflow is not installed.
    """
    if result.status == RunStatus.SKIPPED:
        return None

    mlflow = _import_mlflow()
    mlflow.set_experiment(experiment_name or "fusionflow")

    with mlflow.start_run(run_name=run_name or plan.experiment_name) as run:
        # Log experiment-level params
        mlflow.log_param("fusionflow_experiment", plan.experiment_name)
        mlflow.log_param("fusionflow_timeline", plan.timeline)
        mlflow.log_param("fusionflow_ir_version", plan.ir_version)
        mlflow.log_param("fusionflow_backend", result.backend)
        mlflow.log_param("fusionflow_status", result.status.value)
        mlflow.log_param("model_type", plan.model.type_name)
        mlflow.log_param("model_name", plan.model.name)
        # Log model params (sklearn-style)
        for key, value in plan.model.params.items():
            mlflow.log_param(f"model_param_{key}", value)
        # Log extra params (e.g., {"seed": 42})
        if extra_params:
            for key, value in extra_params.items():
                mlflow.log_param(key, value)

        # Log metrics
        for metric_name, metric_value in result.metrics.items():
            mlflow.log_metric(metric_name, float(metric_value))

        # Log the full RunResult JSON as an artifact
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "run.json"
            artifact_path.write_text(result.to_json())
            mlflow.log_artifact(str(artifact_path))

        return run.info.run_id
