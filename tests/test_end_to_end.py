import json
from pathlib import Path

import pytest

from fusionflow import __main__ as cli
from fusionflow.interpreter import Interpreter
from fusionflow.ir_export import build_temporal_ir
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


FULL_SPEC = """
    dataset customers v1
        source "customers.csv"
        schema { id: int }
    end

    pipeline churn_features
        from customers v1
        derive spend_per_day = amount / days
        select [spend_per_day]
        target churned
    end

    model rf_v1
        type random_forest
        params { trees: 200 }
    end

    experiment churn_baseline
        uses pipeline churn_features
        uses model rf_v1
        metrics [accuracy]
    end

    timeline v2 "Interaction features"
        experiment churn_interaction
            uses pipeline churn_features
            uses model rf_v1
            metrics [accuracy, f1]
            extend {
                derive age_spend = age * spend_per_day
            }
        end
    end

    merge v2 into main
        because "Higher f1 with stable accuracy"
        strategy prefer_metrics f1
    end
    """


def execute_source(source: str) -> Runtime:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(ast)
    return runtime


def test_execute_full_spec():
    runtime = execute_source(FULL_SPEC)

    dataset_key = ("customers", "v1")
    assert dataset_key in runtime.datasets
    assert "churn_features" in runtime.pipelines
    assert "rf_v1" in runtime.models
    main_timeline = runtime.timelines["main"]
    assert "churn_baseline" in main_timeline.experiments
    assert "v2" in runtime.timelines
    assert "churn_interaction" in runtime.timelines["v2"].experiments
    assert runtime.merges and runtime.merges[0].strategy.name == "prefer_metrics"


def test_experiment_requires_known_pipeline():
    source = """
    model rf_v1
        type random_forest
    end

    experiment invalid_exp
        uses pipeline missing
        uses model rf_v1
        metrics [accuracy]
    end
    """

    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    runtime = Runtime()
    interpreter = Interpreter(runtime)

    with pytest.raises(ValueError):
        interpreter.execute(ast)


def test_experiment_requires_known_model():
    source = """
    dataset customers v1
        source "customers.csv"
    end

    pipeline churn_features
        from customers v1
    end

    experiment invalid_exp
        uses pipeline churn_features
        uses model missing
        metrics [accuracy]
    end
    """

    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    runtime = Runtime()
    interpreter = Interpreter(runtime)

    with pytest.raises(ValueError):
        interpreter.execute(ast)


def test_build_temporal_ir_payload():
    runtime = execute_source(FULL_SPEC)
    payload = build_temporal_ir(runtime)

    assert "customers:v1" in payload["datasets"]
    dataset_entry = payload["datasets"]["customers:v1"]
    assert dataset_entry["schema"]["id"] == "int"

    assert "churn_features" in payload["pipelines"]
    pipeline_entry = payload["pipelines"]["churn_features"]
    assert pipeline_entry["operations"][0]["type"] == "derive"

    assert "rf_v1" in payload["models"]
    assert payload["models"]["rf_v1"]["type"] == "random_forest"

    assert "churn_baseline" in payload["experiments"]
    experiment_entry = payload["experiments"]["churn_baseline"]
    assert experiment_entry["pipeline"] == "churn_features"
    assert "extension" not in experiment_entry

    timeline_entry = payload["timelines"]["v2"]
    assert "churn_interaction" in timeline_entry["experiments"]
    extension_steps = timeline_entry["experiments"]["churn_interaction"]["extension"]
    assert extension_steps[0]["target"] == "age_spend"

    assert payload["merges"]
    assert payload["merges"][0]["strategy"]["name"] == "prefer_metrics"


def test_cli_compile_emits_json(tmp_path: Path):
    spec_path = tmp_path / "full_spec.ff"
    spec_path.write_text(FULL_SPEC, encoding="utf-8")
    out_path = tmp_path / "full_spec.tir.json"

    exit_code = cli.main(["compile", str(spec_path), "--out", str(out_path)])

    assert exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["pipelines"]["churn_features"]["operations"][0]["type"] == "derive"
