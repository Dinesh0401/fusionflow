"""Tests for the v0.5 merge algorithm (conflict detection + strategy resolution)."""

import pytest

from fusionflow.merge_algorithm import (
    KNOWN_STRATEGIES,
    MergeConflict,
    MergeStrategyError,
    detect_conflicts,
    merge_ir,
    merge_timelines,
)


def _make_ir(datasets=None, pipelines=None, models=None, experiments=None, timelines=None, merges=None):
    return {
        "ir_version": "0.4",
        "datasets": datasets or {},
        "pipelines": pipelines or {},
        "models": models or {},
        "experiments": experiments or {},
        "timelines": timelines or {},
        "merges": merges or [],
    }


def test_detect_no_conflicts_for_identical_ir():
    ir = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "x.csv", "schema": {}}})
    assert detect_conflicts(ir, ir) == []


def test_detect_no_conflicts_for_disjoint_irs():
    """If source adds new keys not in target, that is NOT a conflict."""
    source = _make_ir(datasets={"a:v1": {"name": "a", "version": "v1", "source": "a.csv", "schema": {}}})
    target = _make_ir(datasets={"b:v1": {"name": "b", "version": "v1", "source": "b.csv", "schema": {}}})
    assert detect_conflicts(source, target) == []


def test_detect_dataset_drift_conflict():
    source = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "new.csv", "schema": {}}})
    target = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "old.csv", "schema": {}}})
    conflicts = detect_conflicts(source, target)
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.section == "datasets"
    assert c.key == "d:v1"
    assert c.conflict_type == "dataset_drift"
    assert c.source_value["source"] == "new.csv"
    assert c.target_value["source"] == "old.csv"


def test_detect_pipeline_drift_lists_op_changes():
    source = _make_ir(pipelines={"p": {"name": "p", "input": "d:v1", "operations": [{"type": "derive", "target": "y", "expression": "x + 1"}]}})
    target = _make_ir(pipelines={"p": {"name": "p", "input": "d:v1", "operations": [{"type": "derive", "target": "y", "expression": "x"}]}})
    conflicts = detect_conflicts(source, target)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "pipeline_drift"
    assert "operations" in conflicts[0].detail


def test_merge_ir_prefer_target_keeps_target_on_conflict():
    source = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "new.csv", "schema": {}}})
    target = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "old.csv", "schema": {}}})
    merged = merge_ir(source, target, strategy="prefer_target")
    assert merged["datasets"]["d:v1"]["source"] == "old.csv"


def test_merge_ir_prefer_source_overrides_target():
    source = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "new.csv", "schema": {}}})
    target = _make_ir(datasets={"d:v1": {"name": "d", "version": "v1", "source": "old.csv", "schema": {}}})
    merged = merge_ir(source, target, strategy="prefer_source")
    assert merged["datasets"]["d:v1"]["source"] == "new.csv"


def test_merge_ir_brings_in_source_only_keys():
    """Keys present only in source are always added to the merged result."""
    source = _make_ir(pipelines={"new_p": {"name": "new_p", "input": "d:v1", "operations": []}})
    target = _make_ir()
    merged = merge_ir(source, target, strategy="prefer_target")
    assert "new_p" in merged["pipelines"]


def test_merge_ir_preserves_target_only_keys():
    """Keys present only in target are always kept."""
    source = _make_ir()
    target = _make_ir(pipelines={"target_p": {"name": "target_p", "input": "d:v1", "operations": []}})
    merged = merge_ir(source, target, strategy="prefer_source")
    assert "target_p" in merged["pipelines"]


def test_merge_ir_unknown_strategy_raises():
    with pytest.raises(MergeStrategyError, match="Unknown merge strategy"):
        merge_ir(_make_ir(), _make_ir(), strategy="prefer_chaos")


def test_merge_ir_prefer_metrics_picks_source_when_source_has_preferred():
    """Experiments conflict, source contains the preferred metric."""
    source = _make_ir(experiments={
        "e": {"pipeline": "p", "model": "m", "metrics": ["f1"]},
    })
    target = _make_ir(experiments={
        "e": {"pipeline": "p", "model": "m", "metrics": ["accuracy"]},
    })
    merged = merge_ir(source, target, strategy="prefer_metrics", strategy_arguments=["f1"])
    assert merged["experiments"]["e"]["metrics"] == ["f1"]


def test_merge_ir_prefer_metrics_falls_back_to_target_when_neither_has_preferred():
    source = _make_ir(experiments={"e": {"pipeline": "p", "model": "m", "metrics": ["accuracy"]}})
    target = _make_ir(experiments={"e": {"pipeline": "p", "model": "m", "metrics": ["rmse"]}})
    merged = merge_ir(source, target, strategy="prefer_metrics", strategy_arguments=["f1"])
    assert merged["experiments"]["e"]["metrics"] == ["rmse"]  # target wins fallback


def test_known_strategies_set():
    assert "prefer_source" in KNOWN_STRATEGIES
    assert "prefer_target" in KNOWN_STRATEGIES
    assert "prefer_metrics" in KNOWN_STRATEGIES


def test_back_compat_merge_timelines_signature_still_works():
    """The v0.3-era merge_timelines(source, target) signature still produces a dict."""
    source = _make_ir(datasets={"a:v1": {"name": "a", "version": "v1", "source": "a.csv", "schema": {}}})
    target = _make_ir(datasets={"b:v1": {"name": "b", "version": "v1", "source": "b.csv", "schema": {}}})
    merged = merge_timelines(source, target)
    assert "a:v1" in merged["datasets"]
    assert "b:v1" in merged["datasets"]


def test_merges_list_is_unioned():
    """Merge statements on either side end up in the merged result, deduped."""
    common_merge = {"source": "b", "target": "main", "justification": "x", "strategy": {"name": "prefer_metrics", "arguments": ["f1"]}}
    source = _make_ir(merges=[common_merge, {"source": "c", "target": "main", "justification": "y", "strategy": {"name": "prefer_target", "arguments": []}}])
    target = _make_ir(merges=[common_merge])
    merged = merge_ir(source, target, strategy="prefer_target")
    assert len(merged["merges"]) == 2  # common + new from source
