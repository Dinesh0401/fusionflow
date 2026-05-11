"""End-to-end tests for the bundled examples in examples/."""

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


@pytest.mark.parametrize("ff_file", ["iris.ff", "regression.ff", "timeline.ff"])
def test_example_parses_cleanly(ff_file):
    """Every example .ff file must parse + interpret without errors."""
    from fusionflow.interpreter import Interpreter
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source = (EXAMPLES / ff_file).read_text()
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    assert runtime.datasets, f"{ff_file} declared no datasets"
    assert runtime.pipelines, f"{ff_file} declared no pipelines"


def test_iris_example_runs_via_pandas_backend():
    from fusionflow.executor import PandasBackend, RunStatus, load_plan
    from fusionflow.interpreter import Interpreter
    from fusionflow.ir_export import build_temporal_ir
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source = (EXAMPLES / "iris.ff").read_text()
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    plan = load_plan(ir, experiment_name="iris_baseline")
    backend = PandasBackend(seed=42, data_root=EXAMPLES)
    result = backend.execute(plan)
    assert result.status == RunStatus.SUCCESS, result.detail
    assert "accuracy" in result.metrics
    assert 0.0 <= result.metrics["accuracy"] <= 1.0


def test_regression_example_runs_via_pandas_backend():
    from fusionflow.executor import PandasBackend, RunStatus, load_plan
    from fusionflow.interpreter import Interpreter
    from fusionflow.ir_export import build_temporal_ir
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source = (EXAMPLES / "regression.ff").read_text()
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    plan = load_plan(ir, experiment_name="regression_baseline")
    backend = PandasBackend(seed=42, data_root=EXAMPLES)
    result = backend.execute(plan)
    assert result.status == RunStatus.SUCCESS, result.detail
    assert "rmse" in result.metrics
    assert result.metrics["rmse"] >= 0.0


def test_timeline_example_has_two_experiments():
    """The timeline example demonstrates baseline + branch with extension."""
    from fusionflow.interpreter import Interpreter
    from fusionflow.ir_export import build_temporal_ir
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source = (EXAMPLES / "timeline.ff").read_text()
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    # Baseline lives in main timeline
    assert "baseline" in ir["experiments"]
    # tighter_split lives in the branch
    branch = ir["timelines"].get("experiment_branch")
    assert branch is not None
    assert "tighter_split" in branch["experiments"]
    # Extension carries the v0.4 ops
    extension = branch["experiments"]["tighter_split"]["extension"]
    op_types = [op["type"] for op in extension]
    assert "split" in op_types
    assert "checkpoint" in op_types


def test_root_example_ff_parses():
    """The root-level example.ff must parse under v0.4 grammar (regression — was broken pre-task-13)."""
    from fusionflow.interpreter import Interpreter
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source = (REPO_ROOT / "example.ff").read_text()
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    assert "iris" in {name for (name, _v) in runtime.datasets.keys()}


def test_examples_readme_lists_all_files():
    """Hygiene: examples/README.md mentions every .ff file."""
    readme = (EXAMPLES / "README.md").read_text()
    for ff in ("iris.ff", "regression.ff", "timeline.ff", "quickstart.ipynb"):
        assert ff in readme, f"examples/README.md does not mention {ff}"
