"""Hygiene tests for the bundled VS Code extension.

These tests do NOT require VS Code or vsce to be installed — they just
verify the extension's JSON files are well-formed and internally consistent."""

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
EXTENSION = REPO_ROOT / "vscode-fusionflow"


def test_extension_package_json_is_valid():
    pkg = json.loads((EXTENSION / "package.json").read_text())
    assert pkg["name"] == "fusionflow"
    assert pkg["version"] == "0.2.0"
    assert "Snippets" in pkg["categories"]


def test_extension_contributes_snippets():
    pkg = json.loads((EXTENSION / "package.json").read_text())
    snippets = pkg["contributes"].get("snippets", [])
    assert len(snippets) == 1
    assert snippets[0]["language"] == "fusionflow"
    snippets_path = EXTENSION / snippets[0]["path"].lstrip("./")
    assert snippets_path.exists(), f"Snippets file referenced but missing at {snippets_path}"


def test_snippets_file_is_valid_json():
    snippets = json.loads((EXTENSION / "snippets" / "fusionflow.json").read_text())
    # Each snippet must have prefix, body, description
    for name, snip in snippets.items():
        assert "prefix" in snip, f"Snippet {name!r} missing prefix"
        assert "body" in snip, f"Snippet {name!r} missing body"
        assert "description" in snip, f"Snippet {name!r} missing description"
        assert isinstance(snip["body"], list), f"Snippet {name!r} body must be list of strings"


def test_snippets_cover_all_v04_constructs():
    """Every v0.4 top-level construct and pipeline step has a snippet."""
    snippets = json.loads((EXTENSION / "snippets" / "fusionflow.json").read_text())
    prefixes = {snip["prefix"] for snip in snippets.values()}
    expected = {
        "dataset", "pipeline", "model", "experiment", "timeline", "merge",
        "derive", "where", "split", "features", "target", "checkpoint", "select",
    }
    missing = expected - prefixes
    assert not missing, f"Missing snippets for: {sorted(missing)}"


def test_textmate_grammar_includes_v04_keywords():
    grammar = json.loads((EXTENSION / "syntaxes" / "fusionflow.tmLanguage.json").read_text())
    keyword_pattern = next(
        p for p in grammar["repository"]["keywords"]["patterns"]
        if "keyword.control.fusionflow" in p["name"]
    )
    pattern_str = keyword_pattern["match"]
    for kw in ("where", "split", "features", "checkpoint"):
        assert kw in pattern_str, f"v0.4 keyword {kw!r} missing from TextMate grammar"


def test_changelog_documents_v02():
    changelog = (EXTENSION / "CHANGELOG.md").read_text()
    assert "## [0.2.0]" in changelog
    assert "snippets" in changelog.lower()
