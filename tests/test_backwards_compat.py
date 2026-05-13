"""Backwards-compat sweep for v0.4.0."""

from pathlib import Path

import pytest

from fusionflow.executor import load_plan
from fusionflow.executor.ir_loader import IRLoadError
from fusionflow.interpreter import Interpreter
from fusionflow.ir_export import build_temporal_ir
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


REPO_ROOT = Path(__file__).resolve().parents[1]


V03_LEGACY_SPECS = [
    """
    dataset legacy_d v1
        source "tiny.csv"
    end
    pipeline legacy_p
        from legacy_d v1
        derive y = age * 2
        select [age, y]
        target y
    end
    model lin
        type linear_regression
    end
    experiment legacy_exp
        uses pipeline legacy_p
        uses model lin
        metrics [rmse]
    end
    """,
    """
    dataset only_dataset v1
        source "tiny.csv"
        schema { age: int, income: int }
    end
    """,
    """
    dataset d v1
        source "tiny.csv"
    end
    pipeline only_pipeline
        from d v1
        derive doubled = age + age
        target doubled
    end
    model linear
        type linear_regression
        params { fit_intercept: true }
    end
    """,
]


@pytest.mark.parametrize("source", V03_LEGACY_SPECS, ids=["full_experiment", "dataset_only", "pipeline_only"])
def test_v03_spec_still_parses_under_v04(source):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)


def test_v03_ir_loads_with_default_version():
    ir = {
        "datasets": {"d:v1": {"name": "d", "version": "v1", "source": "x.csv", "schema": {}}},
        "pipelines": {"p": {"name": "p", "input": "d:v1", "operations": [
            {"type": "derive", "target": "y", "expression": "age * 2"},
            {"type": "target", "field": "y"},
        ]}},
        "models": {"m": {"type": "linear_regression", "params": {}}},
        "experiments": {"e": {"pipeline": "p", "model": "m", "metrics": ["rmse"]}},
        "timelines": {},
        "merges": [],
    }
    plan = load_plan(ir, experiment_name="e")
    assert plan.ir_version == "0.3"


def test_v04_keywords_as_identifiers_documented():
    """v0.4 reserved keywords break user identifiers. Pin the breakage."""
    bad_specs = [
        'dataset d v1\n    source "x.csv"\n    schema { features: int }\nend\n',
        'dataset d where\n    source "x.csv"\nend\n',
    ]
    for source in bad_specs:
        tokens = Lexer(source).tokenize()
        with pytest.raises(SyntaxError):
            Parser(tokens).parse()


def test_existing_example_files_still_compile():
    targets = [
        REPO_ROOT / "example.ff",
        REPO_ROOT / "examples" / "iris.ff",
        REPO_ROOT / "examples" / "regression.ff",
        REPO_ROOT / "examples" / "timeline.ff",
        REPO_ROOT / "tests" / "fixtures" / "regression.ff",
        REPO_ROOT / "tests" / "fixtures" / "classification.ff",
    ]
    for target in targets:
        assert target.exists(), f"Missing canonical example: {target}"
        source = target.read_text()
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        runtime = Runtime()
        Interpreter(runtime).execute(program)
        ir = build_temporal_ir(runtime)
        assert ir["ir_version"] == "0.4"


def test_v04_only_ops_rejected_in_v03_ir_pipeline():
    ir = {
        "datasets": {"d:v1": {"name": "d", "version": "v1", "source": "x.csv", "schema": {}}},
        "pipelines": {"p": {"name": "p", "input": "d:v1", "operations": [
            {"type": "split", "train_ratio": 0.8},
        ]}},
        "models": {"m": {"type": "linear_regression", "params": {}}},
        "experiments": {"e": {"pipeline": "p", "model": "m", "metrics": ["rmse"]}},
        "timelines": {},
        "merges": [],
    }
    with pytest.raises(IRLoadError, match="v0.4-only"):
        load_plan(ir, experiment_name="e")
