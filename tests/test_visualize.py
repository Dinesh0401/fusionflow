"""Tests for the fusionflow visualize feature."""

import pytest

from fusionflow.visualize import SUPPORTED_FORMATS, VisualizeError, visualize_ir
from fusionflow.interpreter import Interpreter
from fusionflow.ir_export import build_temporal_ir
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


SAMPLE = """
dataset users v1
    source "users.csv"
end

pipeline scoring
    from users v1
    derive y = age + 1
    features [age]
    split 0.8
    target y
end

model linear
    type linear_regression
end

experiment baseline
    uses pipeline scoring
    uses model linear
    metrics [rmse, mae]
end

timeline branch
    experiment tuned
        uses pipeline scoring
        uses model linear
        metrics [rmse]
    end
end

merge branch into main
    because "lower rmse"
    strategy prefer_metrics rmse
end
"""


def _ir(source: str) -> dict:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    return build_temporal_ir(runtime)


def test_visualize_mermaid_contains_graph_header():
    out = visualize_ir(_ir(SAMPLE), fmt="mermaid")
    assert out.startswith("graph TD")


def test_visualize_mermaid_includes_all_node_types():
    out = visualize_ir(_ir(SAMPLE), fmt="mermaid")
    assert "dataset: users:v1" in out
    assert "pipeline: scoring" in out
    assert "model: linear" in out
    assert "experiment: baseline" in out
    assert "experiment: tuned" in out


def test_visualize_mermaid_includes_timeline_and_merge():
    out = visualize_ir(_ir(SAMPLE), fmt="mermaid")
    assert "timeline: main" in out
    assert "timeline: branch" in out
    assert "merge: lower rmse" in out


def test_visualize_dot_is_digraph():
    out = visualize_ir(_ir(SAMPLE), fmt="dot")
    assert out.startswith("digraph fusionflow {")
    assert out.rstrip().endswith("}")


def test_visualize_dot_includes_nodes_and_edges():
    out = visualize_ir(_ir(SAMPLE), fmt="dot")
    assert "dataset: users:v1" in out
    assert "experiment: baseline" in out
    assert "->" in out  # at least one edge


def test_visualize_html_is_standalone_page():
    out = visualize_ir(_ir(SAMPLE), fmt="html")
    assert "<!DOCTYPE html>" in out
    assert "mermaid" in out
    assert "graph TD" in out  # the embedded mermaid body


def test_visualize_rejects_unknown_format():
    with pytest.raises(VisualizeError, match="Unsupported visualize format"):
        visualize_ir(_ir(SAMPLE), fmt="ascii_art")


def test_visualize_handles_minimal_spec():
    """A dataset-only spec still renders without crashing."""
    minimal = '''
    dataset d v1
        source "x.csv"
    end
    '''
    out = visualize_ir(_ir(minimal), fmt="mermaid")
    assert "dataset: d:v1" in out


def test_visualize_experiment_graph_wires_pipeline_to_dataset():
    """The pipeline node connects to its input dataset."""
    out = visualize_ir(_ir(SAMPLE), fmt="mermaid")
    # ds_users_v1 -->|feeds| pipe_scoring
    assert "ds_users_v1" in out
    assert "pipe_scoring" in out
    assert "feeds" in out


def test_supported_formats_constant():
    assert set(SUPPORTED_FORMATS) == {"mermaid", "dot", "html"}
