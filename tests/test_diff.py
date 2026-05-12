"""Tests for the IR-aware semantic diff (v0.5 feature)."""

import json

import pytest

from fusionflow.diff import (
    ChangeDetail,
    IRDiff,
    SectionDiff,
    diff_ir,
    format_diff_human,
    format_diff_json,
)


def _make_ir(datasets=None, pipelines=None, models=None, experiments=None, timelines=None, merges=None, ir_version="0.4"):
    return {
        "ir_version": ir_version,
        "datasets": datasets or {},
        "pipelines": pipelines or {},
        "models": models or {},
        "experiments": experiments or {},
        "timelines": timelines or {},
        "merges": merges or [],
    }


def test_diff_identical_ir_is_empty():
    ir = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "x.csv", "schema": {}}})
    diff = diff_ir(ir, ir)
    assert diff.is_empty


def test_diff_added_dataset():
    before = _make_ir()
    after = _make_ir(datasets={"users:v1": {"name": "users", "version": "v1", "source": "users.csv", "schema": {}}})
    diff = diff_ir(before, after)
    assert diff.datasets.added == ["users:v1"]
    assert diff.datasets.removed == []
    assert diff.datasets.changed == {}


def test_diff_removed_pipeline():
    before = _make_ir(pipelines={"p": {"name": "p", "input": "d:v1", "operations": []}})
    after = _make_ir()
    diff = diff_ir(before, after)
    assert diff.pipelines.removed == ["p"]
    assert diff.pipelines.added == []


def test_diff_changed_pipeline_lists_field_paths():
    before = _make_ir(pipelines={"p": {"name": "p", "input": "d:v1", "operations": [{"type": "derive", "target": "y", "expression": "x"}]}})
    after = _make_ir(pipelines={"p": {"name": "p", "input": "d:v1", "operations": [{"type": "derive", "target": "y", "expression": "x + 1"}]}})
    diff = diff_ir(before, after)
    assert "p" in diff.pipelines.changed
    change = diff.pipelines.changed["p"]
    assert any("operations" in path for path in change.field_changes)


def test_diff_ir_version_change():
    before = _make_ir(ir_version="0.3")
    # v0.3 IR doesn't carry ir_version field in practice, but our test ir does. The before's
    # explicit "0.3" should appear in the diff.
    after = _make_ir(ir_version="0.4")
    diff = diff_ir(before, after)
    assert diff.ir_version_before == "0.3"
    assert diff.ir_version_after == "0.4"
    assert not diff.is_empty  # version difference alone counts


def test_diff_handles_missing_ir_version_as_v03():
    before = {"datasets": {}, "pipelines": {}, "models": {}, "experiments": {}, "timelines": {}, "merges": []}
    after = _make_ir()
    diff = diff_ir(before, after)
    assert diff.ir_version_before == "0.3"
    assert diff.ir_version_after == "0.4"


def test_diff_merges_added():
    before = _make_ir()
    after = _make_ir(merges=[{"source": "branch", "target": "main", "justification": "x", "strategy": {"name": "prefer_metrics", "arguments": ["f1"]}}])
    diff = diff_ir(before, after)
    assert len(diff.merges.added) == 1
    assert diff.merges.added[0]["source"] == "branch"
    assert diff.merges.removed == []


def test_format_diff_human_for_empty_diff():
    ir = _make_ir()
    out = format_diff_human(diff_ir(ir, ir))
    assert "Identical" in out


def test_format_diff_human_shows_sections():
    before = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "x.csv", "schema": {}}})
    after = _make_ir(
        datasets={"d:v2": {"name": "d", "version": "v2", "source": "x.csv", "schema": {}}},
        pipelines={"p": {"name": "p", "input": "d:v2", "operations": []}},
    )
    out = format_diff_human(diff_ir(before, after))
    assert "datasets:" in out
    assert "+ d:v2" in out
    assert "- d:v1" in out
    assert "pipelines:" in out
    assert "+ p" in out


def test_format_diff_json_is_parseable():
    ir = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "x.csv", "schema": {}}})
    diff = diff_ir(_make_ir(), ir)
    payload = json.loads(format_diff_json(diff))
    assert payload["datasets"]["added"] == ["d:v1"]
    assert payload["datasets"]["removed"] == []
    assert payload["ir_version_before"] == "0.4"


def test_diff_end_to_end_via_parser():
    """Real .ff source -> diff. Confirms diff sees parser-produced IR shapes."""
    from fusionflow.interpreter import Interpreter
    from fusionflow.ir_export import build_temporal_ir
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source_a = """
    dataset users v1
        source "users.csv"
    end
    pipeline p
        from users v1
        derive y = age + 1
        target y
    end
    """

    source_b = """
    dataset users v1
        source "users.csv"
    end
    pipeline p
        from users v1
        derive y = age + 2
        target y
    end
    pipeline q
        from users v1
        derive z = age
        target z
    end
    """

    def _ir(src):
        tokens = Lexer(src).tokenize()
        program = Parser(tokens).parse()
        runtime = Runtime()
        Interpreter(runtime).execute(program)
        return build_temporal_ir(runtime)

    diff = diff_ir(_ir(source_a), _ir(source_b))
    assert diff.pipelines.added == ["q"]
    assert "p" in diff.pipelines.changed
