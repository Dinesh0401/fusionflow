"""Hygiene tests for v0.4.0 docs."""

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"


REQUIRED_DOCS = [
    "getting-started.md",
    "cli.md",
    "ir-spec-v0.4.md",
    "backends.md",
]


@pytest.mark.parametrize("doc_name", REQUIRED_DOCS)
def test_required_docs_exist(doc_name):
    path = DOCS / doc_name
    assert path.exists(), f"Required doc missing: {path}"
    assert path.read_text(encoding="utf-8").strip(), f"Doc is empty: {path}"


def test_getting_started_mentions_install_command():
    text = (DOCS / "getting-started.md").read_text(encoding="utf-8")
    assert "pip install fusionflow" in text
    assert "fusionflow run" in text


def test_cli_doc_lists_all_subcommands():
    text = (DOCS / "cli.md").read_text(encoding="utf-8")
    for sub in ("run", "validate", "compile"):
        assert f"`fusionflow {sub}" in text, f"CLI doc missing subcommand: {sub}"


def test_ir_spec_documents_v04_keywords():
    text = (DOCS / "ir-spec-v0.4.md").read_text(encoding="utf-8")
    for op in ("where", "split", "features", "checkpoint"):
        assert f"`{op}`" in text, f"IR spec missing v0.4 op: {op}"
    assert "Reserved keywords" in text or "reserved keywords" in text


def test_backends_doc_documents_model_registry():
    text = (DOCS / "backends.md").read_text(encoding="utf-8")
    for model in ("linear_regression", "logistic_regression", "random_forest_classifier"):
        assert model in text, f"Backends doc missing model: {model}"


def test_root_readme_mentions_v04():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "v0.4" in text or "0.4.0" in text, "Root README does not mention v0.4"
