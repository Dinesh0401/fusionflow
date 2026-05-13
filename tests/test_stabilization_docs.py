"""Hygiene tests for the v0.5 stabilization documents."""

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("filename", [
    "CONTRIBUTING.md",
    "ROADMAP.md",
    "DESIGN_PRINCIPLES.md",
    "ARCHITECTURE_OVERVIEW.md",
    "SYNTAX_FROZEN.md",
])
def test_stabilization_doc_exists_and_nonempty(filename):
    path = REPO_ROOT / filename
    assert path.exists(), f"Required doc missing: {path}"
    assert len(path.read_text(encoding="utf-8")) > 200, f"Doc too short: {path}"


@pytest.mark.parametrize("filename", [
    "examples/churn_prediction.ff",
    "examples/fraud_detection.ff",
    "examples/ab_testing.ff",
    "examples/feature_evolution.ff",
    "examples/timeline_merge_demo.ff",
])
def test_example_ff_files_parse(filename):
    from fusionflow.interpreter import Interpreter
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source = (REPO_ROOT / filename).read_text(encoding="utf-8")
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)


def test_visualize_design_doc_present():
    assert (REPO_ROOT / "docs" / "visualize-design.md").exists()


def test_paper_outline_present():
    assert (REPO_ROOT / "docs" / "paper-outline.md").exists()


def test_demo_script_present():
    assert (REPO_ROOT / "scripts" / "demo-script.md").exists()


def test_syntax_freeze_mentions_v05_cycle():
    text = (REPO_ROOT / "SYNTAX_FROZEN.md").read_text(encoding="utf-8")
    assert "v0.5" in text
    assert "frozen" in text.lower()
