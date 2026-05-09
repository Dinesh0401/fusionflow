"""Tests for Temporal IR v0.4 export determinism and v0.4 step lowering."""

import json

import pytest

from fusionflow.interpreter import Interpreter
from fusionflow.ir_export import build_temporal_ir
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


def _build_ir_from_source(source: str) -> dict:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    return build_temporal_ir(runtime)


def test_ir_includes_version_field():
    source = """
    dataset d v1
        source "x.csv"
    end
    """
    ir = _build_ir_from_source(source)
    assert ir["ir_version"] == "0.4"


def test_ir_serialization_is_deterministic():
    source = """
    dataset users v1
        source "users.csv"
    end
    pipeline p
        from users v1
        derive y = age + 1
        target y
    end
    """
    first = json.dumps(_build_ir_from_source(source))
    second = json.dumps(_build_ir_from_source(source))
    assert first == second


def test_ir_lowers_where_step():
    source = """
    dataset d v1
        source "x.csv"
    end
    pipeline p
        from d v1
        derive adult = age >= 18
        where adult
        target adult
    end
    """
    ir = _build_ir_from_source(source)
    ops = ir["pipelines"]["p"]["operations"]
    where_ops = [op for op in ops if op["type"] == "where"]
    assert len(where_ops) == 1
    assert where_ops[0]["condition"] == "adult"


def test_ir_lowers_split_step():
    source = """
    dataset d v1
        source "x.csv"
    end
    pipeline p
        from d v1
        derive y = 1
        split 0.8
        target y
    end
    """
    ir = _build_ir_from_source(source)
    split_ops = [op for op in ir["pipelines"]["p"]["operations"] if op["type"] == "split"]
    assert len(split_ops) == 1
    assert split_ops[0]["train_ratio"] == 0.8


def test_ir_lowers_features_step():
    source = """
    dataset d v1
        source "x.csv"
    end
    pipeline p
        from d v1
        derive y = 1
        features [a, b, c]
        target y
    end
    """
    ir = _build_ir_from_source(source)
    feat_ops = [op for op in ir["pipelines"]["p"]["operations"] if op["type"] == "features"]
    assert len(feat_ops) == 1
    assert feat_ops[0]["fields"] == ["a", "b", "c"]


def test_ir_lowers_checkpoint_step():
    source = """
    dataset d v1
        source "x.csv"
    end
    pipeline p
        from d v1
        derive y = 1
        checkpoint pre_train
        target y
    end
    """
    ir = _build_ir_from_source(source)
    cp_ops = [op for op in ir["pipelines"]["p"]["operations"] if op["type"] == "checkpoint"]
    assert len(cp_ops) == 1
    assert cp_ops[0]["name"] == "pre_train"


def test_ir_lowers_all_v04_steps_in_extend_block():
    source = """
    dataset d v1
        source "x.csv"
    end
    pipeline p
        from d v1
        derive y = 1
        target y
    end
    model m
        type linear
    end
    timeline branch
        experiment e
            uses pipeline p
            uses model m
            metrics [accuracy]
            extend {
                where y == 1
                features [y]
                split 0.7
                checkpoint mid
            }
        end
    end
    """
    ir = _build_ir_from_source(source)
    ext_ops = ir["timelines"]["branch"]["experiments"]["e"]["extension"]
    op_types = [op["type"] for op in ext_ops]
    assert op_types == ["where", "features", "split", "checkpoint"]


def test_ir_raises_on_unknown_step_type():
    """Sentinel: future step types must be added to _serialize_steps explicitly."""
    from fusionflow.ast_nodes import PipelineStep
    from fusionflow.ir_export import _serialize_steps

    class FakeStep(PipelineStep):
        pass

    with pytest.raises(NotImplementedError, match="FakeStep"):
        _serialize_steps([FakeStep()])
