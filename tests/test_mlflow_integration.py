"""Tests for the MLflow integration.

Mocks the mlflow module so tests run whether or not mlflow is installed."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from fusionflow.executor import (
    DatasetSpec,
    ExecutionPlan,
    ModelSpec,
    PipelineSpec,
    RunResult,
    RunStatus,
)
from fusionflow.integrations.mlflow_logger import (
    MLflowNotInstalledError,
    log_run_result,
)


@pytest.fixture
def fake_plan():
    return ExecutionPlan(
        ir_version="0.4",
        experiment_name="test_exp",
        timeline="main",
        datasets=(DatasetSpec(name="d", version="v1", source="x.csv", schema={}),),
        pipeline=PipelineSpec(name="p", input_dataset="d:v1", ops=()),
        model=ModelSpec(name="m", type_name="linear_regression", params={"fit_intercept": True}),
        metrics=("rmse",),
    )


@pytest.fixture
def fake_result_success():
    return RunResult(
        experiment="test_exp",
        backend="pandas",
        status=RunStatus.SUCCESS,
        ir_version="0.4",
        metrics={"rmse": 1.5, "mae": 1.2},
        detail="ok",
    )


@pytest.fixture
def fake_result_skipped():
    return RunResult(
        experiment="test_exp",
        backend="noop",
        status=RunStatus.SKIPPED,
        ir_version="0.4",
        metrics={},
        detail="noop",
    )


def test_log_run_result_calls_mlflow_apis(fake_plan, fake_result_success):
    fake_mlflow = MagicMock()
    fake_run = MagicMock()
    fake_run.info.run_id = "abc123"
    fake_mlflow.start_run.return_value.__enter__.return_value = fake_run
    fake_mlflow.start_run.return_value.__exit__.return_value = False

    with patch.dict(sys.modules, {"mlflow": fake_mlflow}):
        run_id = log_run_result(plan=fake_plan, result=fake_result_success)

    assert run_id == "abc123"
    fake_mlflow.set_experiment.assert_called_once_with("fusionflow")
    fake_mlflow.start_run.assert_called_once()
    # Verify metrics logged
    assert fake_mlflow.log_metric.call_count == 2
    fake_mlflow.log_metric.assert_any_call("rmse", 1.5)
    fake_mlflow.log_metric.assert_any_call("mae", 1.2)
    # Verify some params logged
    fake_mlflow.log_param.assert_any_call("fusionflow_experiment", "test_exp")
    fake_mlflow.log_param.assert_any_call("fusionflow_ir_version", "0.4")
    fake_mlflow.log_param.assert_any_call("model_type", "linear_regression")
    fake_mlflow.log_param.assert_any_call("model_param_fit_intercept", True)
    # Verify artifact logged
    assert fake_mlflow.log_artifact.call_count == 1


def test_log_run_result_skips_skipped_status(fake_plan, fake_result_skipped):
    """SKIPPED runs should NOT create an MLflow run."""
    fake_mlflow = MagicMock()
    with patch.dict(sys.modules, {"mlflow": fake_mlflow}):
        run_id = log_run_result(plan=fake_plan, result=fake_result_skipped)
    assert run_id is None
    fake_mlflow.start_run.assert_not_called()


def test_log_run_result_passes_extra_params(fake_plan, fake_result_success):
    fake_mlflow = MagicMock()
    fake_mlflow.start_run.return_value.__enter__.return_value = MagicMock(
        info=MagicMock(run_id="r")
    )

    with patch.dict(sys.modules, {"mlflow": fake_mlflow}):
        log_run_result(
            plan=fake_plan,
            result=fake_result_success,
            extra_params={"seed": 42, "num_threads": 1},
        )

    fake_mlflow.log_param.assert_any_call("seed", 42)
    fake_mlflow.log_param.assert_any_call("num_threads", 1)


def test_log_run_result_uses_custom_experiment_name(fake_plan, fake_result_success):
    fake_mlflow = MagicMock()
    fake_mlflow.start_run.return_value.__enter__.return_value = MagicMock(
        info=MagicMock(run_id="r")
    )

    with patch.dict(sys.modules, {"mlflow": fake_mlflow}):
        log_run_result(
            plan=fake_plan,
            result=fake_result_success,
            experiment_name="my_custom_exp",
        )

    fake_mlflow.set_experiment.assert_called_once_with("my_custom_exp")


def test_log_run_result_raises_when_mlflow_missing(fake_plan, fake_result_success):
    """If mlflow module isn't available, raise a clear install-hint error."""
    # Remove mlflow from sys.modules and patch __import__ to fail
    if "mlflow" in sys.modules:
        del sys.modules["mlflow"]

    real_import = (
        __builtins__["__import__"]
        if isinstance(__builtins__, dict)
        else __builtins__.__import__
    )

    def fake_import(name, *args, **kwargs):
        if name == "mlflow":
            raise ImportError("No module named 'mlflow'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        with pytest.raises(MLflowNotInstalledError, match="pip install fusionflow\\[mlflow\\]"):
            log_run_result(plan=fake_plan, result=fake_result_success)
