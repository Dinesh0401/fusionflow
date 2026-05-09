"""Tests for the v0.4 executor skeleton (plan loading, Protocol, NoopBackend)."""

import pytest

from fusionflow.executor import (
    ExecutionPlan,
    NoopBackend,
    Op,
    SplitOp,
    TrainOp,
    EvalOp,
    load_plan,
)
from fusionflow.executor.ir_loader import IRLoadError, SUPPORTED_IR_VERSIONS
from fusionflow.executor.run_result import RunStatus
from fusionflow.interpreter import Interpreter
from fusionflow.ir_export import build_temporal_ir
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


def _ir_from_source(source: str) -> dict:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    return build_temporal_ir(runtime)


SAMPLE_SOURCE = """
dataset users v1
    source "users.csv"
    schema {
        age: int,
        income: float
    }
end

pipeline scoring
    from users v1
    derive bonus = income * 0.1
    where age >= 18
    features [age, bonus]
    split 0.8
    target bonus
end

model linear
    type linear_regression
    params { fit_intercept: true }
end

experiment baseline
    uses pipeline scoring
    uses model linear
    metrics [rmse, mae]
end
"""


def test_load_plan_returns_execution_plan():
    ir = _ir_from_source(SAMPLE_SOURCE)
    plan = load_plan(ir, experiment_name="baseline")
    assert isinstance(plan, ExecutionPlan)
    assert plan.experiment_name == "baseline"
    assert plan.timeline == "main"
    assert plan.ir_version == "0.4"


def test_load_plan_resolves_pipeline_and_model():
    ir = _ir_from_source(SAMPLE_SOURCE)
    plan = load_plan(ir, experiment_name="baseline")
    assert plan.pipeline.name == "scoring"
    assert plan.pipeline.input_dataset == "users:v1"
    assert plan.model.name == "linear"
    assert plan.model.type_name == "linear_regression"


def test_load_plan_appends_train_and_eval_ops():
    ir = _ir_from_source(SAMPLE_SOURCE)
    plan = load_plan(ir, experiment_name="baseline")
    ops = plan.all_ops
    assert isinstance(ops[-2], TrainOp)
    assert isinstance(ops[-1], EvalOp)
    assert ops[-1].metrics == ("rmse", "mae")


def test_load_plan_includes_extension_ops():
    source = SAMPLE_SOURCE + """
timeline branch
    experiment tuned
        uses pipeline scoring
        uses model linear
        metrics [rmse]
        extend {
            split 0.7
            checkpoint mid
        }
    end
end
"""
    ir = _ir_from_source(source)
    plan = load_plan(ir, experiment_name="tuned")
    assert plan.timeline == "branch"
    # Last two ops are TrainOp + EvalOp; before them should be the extension ops
    extension_op_types = [type(op).__name__ for op in plan.extension_ops]
    assert "SplitOp" in extension_op_types
    assert "CheckpointOp" in extension_op_types


def test_load_plan_rejects_unknown_ir_version():
    ir = {"ir_version": "9.9", "datasets": {}, "pipelines": {}, "models": {}, "experiments": {}, "timelines": {}, "merges": []}
    with pytest.raises(IRLoadError, match="Unsupported IR version"):
        load_plan(ir, experiment_name="anything")


def test_load_plan_treats_missing_ir_version_as_v03():
    """v0.3 IR predates the field; the loader treats missing as '0.3'."""
    ir = {
        "datasets": {"d:v1": {"name": "d", "version": "v1", "source": "x", "schema": {}}},
        "pipelines": {"p": {"name": "p", "input": "d:v1", "operations": [{"type": "derive", "target": "y", "expression": "1"}]}},
        "models": {"m": {"type": "linear", "params": {}}},
        "experiments": {"e": {"pipeline": "p", "model": "m", "metrics": ["acc"]}},
        "timelines": {},
        "merges": [],
    }
    plan = load_plan(ir, experiment_name="e")
    assert plan.ir_version == "0.3"


def test_load_plan_rejects_v04_ops_in_v03_ir():
    """Defensive: hand-edited v0.3 IR with new ops should fail loudly."""
    ir = {
        "datasets": {"d:v1": {"name": "d", "version": "v1", "source": "x", "schema": {}}},
        "pipelines": {"p": {"name": "p", "input": "d:v1", "operations": [{"type": "split", "train_ratio": 0.8}]}},
        "models": {"m": {"type": "linear", "params": {}}},
        "experiments": {"e": {"pipeline": "p", "model": "m", "metrics": ["acc"]}},
        "timelines": {},
        "merges": [],
    }
    with pytest.raises(IRLoadError, match="v0.4-only operation"):
        load_plan(ir, experiment_name="e")


def test_load_plan_raises_on_unknown_experiment():
    ir = _ir_from_source(SAMPLE_SOURCE)
    with pytest.raises(IRLoadError, match="not found in IR"):
        load_plan(ir, experiment_name="nonexistent")


def test_load_plan_raises_on_unknown_op_type():
    """The IR loader rejects unknown op types loudly (mirror of ir_export's catch-all)."""
    from fusionflow.executor.ir_loader import _load_op
    with pytest.raises(IRLoadError, match="Unknown IR operation type"):
        _load_op({"type": "some_future_op", "field": "x"})


def test_noop_backend_runs_supported_plan():
    ir = _ir_from_source(SAMPLE_SOURCE)
    plan = load_plan(ir, experiment_name="baseline")
    backend = NoopBackend()
    report = backend.supports(plan)
    assert report.supported
    assert report.unsupported_ops == []

    result = backend.execute(plan)
    assert result.experiment == "baseline"
    assert result.backend == "noop"
    assert result.status == RunStatus.SKIPPED
    assert result.ir_version == "0.4"


def test_noop_backend_to_json_is_deterministic():
    ir = _ir_from_source(SAMPLE_SOURCE)
    plan = load_plan(ir, experiment_name="baseline")
    backend = NoopBackend()
    first = backend.execute(plan).to_json()
    second = backend.execute(plan).to_json()
    assert first == second


def test_noop_backend_reports_unsupported_ops():
    """Sentinel: if a future Op subclass slips in without NoopBackend support,
    NoopBackend should refuse and explain why."""
    from fusionflow.executor.plan import (
        DatasetSpec, ExecutionPlan, ModelSpec, PipelineSpec, Op,
    )

    class FutureOp(Op):
        pass

    plan = ExecutionPlan(
        ir_version="0.4",
        experiment_name="x",
        timeline="main",
        datasets=(),
        pipeline=PipelineSpec(name="p", input_dataset="d:v1", ops=(FutureOp(),)),
        model=ModelSpec(name="m", type_name="linear_regression", params={}),
        metrics=("acc",),
    )
    backend = NoopBackend()
    report = backend.supports(plan)
    assert not report.supported
    assert "FutureOp" in report.unsupported_ops

    result = backend.execute(plan)
    assert result.status == RunStatus.FAILED
    assert "FutureOp" in result.detail
