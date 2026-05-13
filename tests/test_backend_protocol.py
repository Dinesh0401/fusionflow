"""Contract tests for ExecutionBackend implementations."""

from pathlib import Path

import pytest

from fusionflow.executor import (
    DatasetSpec, ExecutionBackend, ExecutionPlan, ModelSpec,
    NoopBackend, PandasBackend, PipelineSpec, RunResult, SupportReport,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _make_minimal_plan() -> ExecutionPlan:
    return ExecutionPlan(
        ir_version="0.4",
        experiment_name="contract_test",
        timeline="main",
        datasets=(DatasetSpec(name="d", version="v1", source="tiny.csv", schema={}),),
        pipeline=PipelineSpec(name="p", input_dataset="d:v1", ops=()),
        model=ModelSpec(name="m", type_name="linear_regression", params={"fit_intercept": True}),
        metrics=("rmse",),
    )


@pytest.fixture(params=[
    pytest.param(lambda: NoopBackend(), id="noop"),
    pytest.param(lambda: PandasBackend(seed=42, data_root=FIXTURES), id="pandas"),
])
def backend(request):
    return request.param()


def test_backend_is_instance_of_protocol(backend):
    assert isinstance(backend, ExecutionBackend)


def test_backend_has_name(backend):
    assert isinstance(backend.name, str) and backend.name


def test_backend_supports_returns_support_report(backend):
    plan = _make_minimal_plan()
    report = backend.supports(plan)
    assert isinstance(report, SupportReport)


def test_backend_execute_returns_run_result(backend):
    plan = _make_minimal_plan()
    result = backend.execute(plan)
    assert isinstance(result, RunResult)
    assert result.experiment == "contract_test"
    assert result.backend == backend.name


def test_backend_execute_never_returns_none(backend):
    plan = _make_minimal_plan()
    result = backend.execute(plan)
    assert result is not None
