"""End-to-end tests for the Pandas backend (v0.4 headline feature)."""

from pathlib import Path

import pytest

from fusionflow.executor import PandasBackend, RunStatus, load_plan
from fusionflow.interpreter import Interpreter
from fusionflow.ir_export import build_temporal_ir
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


FIXTURES = Path(__file__).parent / "fixtures"


def _ir_from_file(path: Path) -> dict:
    source = path.read_text()
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    return build_temporal_ir(runtime)


def _ir_from_source(source: str) -> dict:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    return build_temporal_ir(runtime)


@pytest.fixture
def regression_plan():
    ir = _ir_from_file(FIXTURES / "regression.ff")
    return load_plan(ir, experiment_name="regression_baseline")


@pytest.fixture
def classification_plan():
    ir = _ir_from_file(FIXTURES / "classification.ff")
    return load_plan(ir, experiment_name="churn_baseline")


def test_pandas_backend_supports_known_plan(regression_plan):
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    report = backend.supports(regression_plan)
    assert report.supported, report.reason


def test_pandas_backend_runs_regression(regression_plan):
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    result = backend.execute(regression_plan)
    assert result.status == RunStatus.SUCCESS, result.detail
    assert result.experiment == "regression_baseline"
    assert result.backend == "pandas"
    assert result.ir_version == "0.4"
    assert "rmse" in result.metrics
    assert "mae" in result.metrics
    assert result.metrics["rmse"] >= 0.0
    assert result.metrics["mae"] >= 0.0


def test_pandas_backend_runs_classification(classification_plan):
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    result = backend.execute(classification_plan)
    assert result.status == RunStatus.SUCCESS, result.detail
    assert "accuracy" in result.metrics
    assert "f1" in result.metrics
    assert 0.0 <= result.metrics["accuracy"] <= 1.0
    assert 0.0 <= result.metrics["f1"] <= 1.0


def test_pandas_backend_is_deterministic(regression_plan):
    """Two runs with same seed produce byte-identical RunResult.to_json()."""
    first = PandasBackend(seed=42, data_root=FIXTURES).execute(regression_plan).to_json()
    second = PandasBackend(seed=42, data_root=FIXTURES).execute(regression_plan).to_json()
    assert first == second


def test_pandas_backend_different_seed_changes_metrics(regression_plan):
    """Different seeds should change train/test split (and thus metrics)."""
    a = PandasBackend(seed=42, data_root=FIXTURES).execute(regression_plan).metrics
    b = PandasBackend(seed=99, data_root=FIXTURES).execute(regression_plan).metrics
    assert a != b


def test_pandas_backend_rejects_unknown_model():
    """Plan with an unknown model.type_name fails at supports() before execute."""
    from fusionflow.executor.plan import (
        DatasetSpec,
        ExecutionPlan,
        ModelSpec,
        PipelineSpec,
    )

    plan = ExecutionPlan(
        ir_version="0.4",
        experiment_name="x",
        timeline="main",
        datasets=(DatasetSpec(name="d", version="v1", source="tiny.csv", schema={}),),
        pipeline=PipelineSpec(name="p", input_dataset="d:v1", ops=()),
        model=ModelSpec(name="m", type_name="rocket_science_model_9000", params={}),
        metrics=("rmse",),
    )
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    report = backend.supports(plan)
    assert not report.supported
    assert any("rocket_science_model_9000" in u for u in report.unsupported_ops)


def test_pandas_backend_rejects_unknown_metric():
    """Plan with an unknown metric name fails at supports()."""
    from fusionflow.executor.plan import (
        DatasetSpec,
        ExecutionPlan,
        ModelSpec,
        PipelineSpec,
    )

    plan = ExecutionPlan(
        ir_version="0.4",
        experiment_name="x",
        timeline="main",
        datasets=(DatasetSpec(name="d", version="v1", source="tiny.csv", schema={}),),
        pipeline=PipelineSpec(name="p", input_dataset="d:v1", ops=()),
        model=ModelSpec(name="m", type_name="linear_regression", params={}),
        metrics=("ultranormalcrossentropy",),
    )
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    report = backend.supports(plan)
    assert not report.supported
    assert any("ultranormalcrossentropy" in u for u in report.unsupported_ops)


def test_pandas_backend_handles_where_filter():
    """A pipeline with a WHERE clause filters rows before training."""
    source = """
    dataset customers v1
        source "tiny.csv"
    end
    pipeline filtered
        from customers v1
        where age >= 30
        features [age, income]
        split 0.7
        target spend
    end
    model linear
        type linear_regression
    end
    experiment filtered_baseline
        uses pipeline filtered
        uses model linear
        metrics [rmse]
    end
    """
    ir = _ir_from_source(source)
    plan = load_plan(ir, experiment_name="filtered_baseline")
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    result = backend.execute(plan)
    assert result.status == RunStatus.SUCCESS, result.detail
    assert result.metrics["rmse"] >= 0.0


def test_pandas_backend_uses_all_columns_when_features_missing():
    """If FeaturesOp is omitted, backend defaults to 'all columns except target'."""
    source = """
    dataset customers v1
        source "tiny.csv"
    end
    pipeline default_features
        from customers v1
        select [age, income, spend]
        split 0.7
        target spend
    end
    model linear
        type linear_regression
    end
    experiment default_baseline
        uses pipeline default_features
        uses model linear
        metrics [rmse]
    end
    """
    ir = _ir_from_source(source)
    plan = load_plan(ir, experiment_name="default_baseline")
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    result = backend.execute(plan)
    assert result.status == RunStatus.SUCCESS, result.detail


def test_pandas_backend_fails_without_target():
    """A plan without a TargetOp must fail at execute time with a clear message."""
    source = """
    dataset customers v1
        source "tiny.csv"
    end
    pipeline no_target
        from customers v1
        features [age, income]
        split 0.7
    end
    model linear
        type linear_regression
    end
    experiment notarget_baseline
        uses pipeline no_target
        uses model linear
        metrics [rmse]
    end
    """
    ir = _ir_from_source(source)
    plan = load_plan(ir, experiment_name="notarget_baseline")
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    result = backend.execute(plan)
    assert result.status == RunStatus.FAILED
    assert "target" in result.detail.lower()


def test_pandas_backend_respects_fit_intercept_false():
    """Critical regression: fit_intercept: false must actually disable the intercept.
    Pre-fix, _coerce_linear_params did bool('false')==True and silently flipped this."""
    source = """
    dataset customers v1
        source "tiny.csv"
    end
    pipeline regression_pipe
        from customers v1
        features [age, income]
        split 0.7
        target spend
    end
    model lin_no_intercept
        type linear_regression
        params { fit_intercept: false }
    end
    experiment no_intercept
        uses pipeline regression_pipe
        uses model lin_no_intercept
        metrics [rmse]
    end
    """
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    plan = load_plan(ir, experiment_name="no_intercept")
    backend = PandasBackend(seed=42, data_root=FIXTURES)
    result = backend.execute(plan)
    assert result.status == RunStatus.SUCCESS, result.detail

    # Compare against the with-intercept baseline; metrics must differ.
    intercept_source = source.replace("fit_intercept: false", "fit_intercept: true")
    tokens2 = Lexer(intercept_source).tokenize()
    program2 = Parser(tokens2).parse()
    runtime2 = Runtime()
    Interpreter(runtime2).execute(program2)
    ir2 = build_temporal_ir(runtime2)
    plan2 = load_plan(ir2, experiment_name="no_intercept")
    result2 = PandasBackend(seed=42, data_root=FIXTURES).execute(plan2)

    assert result.metrics["rmse"] != result2.metrics["rmse"], \
        f"fit_intercept: false produced same metrics as true ({result.metrics['rmse']}); coercion is broken"


def test_pandas_backend_returns_failed_on_missing_csv(tmp_path):
    """Plan with a missing dataset file must return FAILED RunResult, not raise."""
    source = """
    dataset ghost v1
        source "does_not_exist.csv"
    end
    pipeline p
        from ghost v1
        features [a]
        split 0.7
        target b
    end
    model lin
        type linear_regression
    end
    experiment e
        uses pipeline p
        uses model lin
        metrics [rmse]
    end
    """
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    plan = load_plan(ir, experiment_name="e")
    backend = PandasBackend(seed=42, data_root=tmp_path)  # tmp_path is empty
    result = backend.execute(plan)
    assert result.status == RunStatus.FAILED
    assert "does_not_exist.csv" in result.detail or "FileNotFoundError" in result.detail


def test_pandas_backend_rejects_unknown_model_params():
    """Unknown params must raise UnknownModelTypeError at build time, surfacing user intent."""
    from fusionflow.executor.models import build_model, UnknownModelTypeError

    with pytest.raises(UnknownModelTypeError, match="Unknown params"):
        build_model("linear_regression", {"criterion": "gini"}, seed=42)

    with pytest.raises(UnknownModelTypeError, match="Unknown params"):
        build_model("random_forest_classifier", {"min_samples_split": 5}, seed=42)
