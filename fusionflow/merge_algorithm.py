"""Timeline merge conflict detection for FusionFlow.

Given two `Runtime` snapshots (typically the source timeline state and the
target timeline state of a `merge X into Y` statement), detect conflicts: same
key, different content. Apply resolution strategies (`prefer_source`,
`prefer_target`, `prefer_metrics`) to produce a merged Runtime.

The decision tree is intentionally structural — there's no execution of the
underlying ML pipeline. The algorithm operates on the IR shape, so v0.6+
backends (Spark, Polars) can reuse the same merge logic without re-deriving it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from fusionflow.diff import IRDiff, diff_ir


CONFLICT_TYPES = {
    "datasets": "dataset_drift",
    "pipelines": "pipeline_drift",
    "models": "model_drift",
    "experiments": "experiment_drift",
    "timelines": "timeline_drift",
}


@dataclass
class MergeConflict:
    """A single conflict between source and target timeline states.

    `section` is one of datasets / pipelines / models / experiments / timelines.
    `key` is the identifier (e.g., "users:v1" for datasets, "scoring" for pipelines).
    `conflict_type` is a stable string for tooling to switch on.
    """

    section: str
    key: str
    conflict_type: str
    source_value: Dict[str, Any]
    target_value: Dict[str, Any]
    detail: str = ""


class MergeStrategyError(ValueError):
    """Raised when a strategy cannot resolve a conflict."""


KNOWN_STRATEGIES = frozenset({"prefer_source", "prefer_target", "prefer_metrics"})


def detect_conflicts(source_ir: Dict[str, Any], target_ir: Dict[str, Any]) -> List[MergeConflict]:
    """Compare two IR dicts and return the list of structural conflicts.

    Conflicts arise when both sides declare the same key but with different
    content. Additions (only on source) and removals (only on target) are NOT
    conflicts — they are merge inputs and end up in the merged result.
    """
    diff: IRDiff = diff_ir(target_ir, source_ir)  # before=target, after=source
    conflicts: List[MergeConflict] = []
    for section_name, conflict_label in CONFLICT_TYPES.items():
        section_diff = getattr(diff, section_name)
        for key, change in section_diff.changed.items():
            conflicts.append(
                MergeConflict(
                    section=section_name,
                    key=key,
                    conflict_type=conflict_label,
                    source_value=change.after,
                    target_value=change.before,
                    detail=", ".join(change.field_changes) or "(content differs)",
                )
            )
    return conflicts


def merge_ir(
    source_ir: Dict[str, Any],
    target_ir: Dict[str, Any],
    strategy: str = "prefer_target",
    strategy_arguments: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Merge `source_ir` into `target_ir` according to the named strategy.

    Strategies:
      - `prefer_source` : on conflict, take the source side.
      - `prefer_target` : on conflict, take the target side (the default — safe).
      - `prefer_metrics`: on experiment conflicts, prefer the side whose first
                          metric appears in `strategy_arguments`. On other
                          sections, falls back to `prefer_target`.
    """
    if strategy not in KNOWN_STRATEGIES:
        raise MergeStrategyError(
            f"Unknown merge strategy: {strategy!r}. "
            f"Supported: {sorted(KNOWN_STRATEGIES)}."
        )

    strategy_arguments = list(strategy_arguments or [])
    merged: Dict[str, Any] = {
        "ir_version": target_ir.get("ir_version", source_ir.get("ir_version", "0.4")),
        "datasets": dict(target_ir.get("datasets", {})),
        "pipelines": dict(target_ir.get("pipelines", {})),
        "models": dict(target_ir.get("models", {})),
        "experiments": dict(target_ir.get("experiments", {})),
        "timelines": dict(target_ir.get("timelines", {})),
        "merges": list(target_ir.get("merges", [])),
    }

    # Adds (keys only on source) always come over.
    # Conflicts are resolved by strategy.
    for section in ("datasets", "pipelines", "models", "experiments", "timelines"):
        source_section: Dict[str, Any] = source_ir.get(section, {})
        target_section: Dict[str, Any] = target_ir.get(section, {})
        for key, source_value in source_section.items():
            if key not in target_section:
                merged[section][key] = source_value
                continue
            target_value = target_section[key]
            if source_value == target_value:
                continue
            # Conflict path
            if strategy == "prefer_source":
                merged[section][key] = source_value
            elif strategy == "prefer_target":
                merged[section][key] = target_value
            elif strategy == "prefer_metrics":
                merged[section][key] = _resolve_metrics_preference(
                    section, key, source_value, target_value, strategy_arguments,
                )

    # Merges list: union both sides (deduped by full content).
    merged["merges"] = _union_merges(
        target_ir.get("merges", []), source_ir.get("merges", []),
    )
    return merged


def _resolve_metrics_preference(
    section: str,
    key: str,
    source_value: Dict[str, Any],
    target_value: Dict[str, Any],
    preferred_metrics: List[str],
) -> Dict[str, Any]:
    """For experiment conflicts under `prefer_metrics`, pick the side whose
    metrics list contains the first preferred metric. Fallback: target."""
    if section != "experiments":
        return target_value
    source_metrics = set(source_value.get("metrics", []))
    target_metrics = set(target_value.get("metrics", []))
    for metric in preferred_metrics:
        if metric in source_metrics and metric not in target_metrics:
            return source_value
        if metric in target_metrics and metric not in source_metrics:
            return target_value
    return target_value


def _union_merges(target_merges: List[Dict[str, Any]], source_merges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    import json
    seen = set()
    result: List[Dict[str, Any]] = []
    for merge in list(target_merges) + list(source_merges):
        key = json.dumps(merge, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(merge)
    return result


# Back-compat wrappers (for the v0.3-era signature; takes dict-like state).
def merge_timelines(source_state: Dict[str, Any], target_state: Dict[str, Any]) -> Dict[str, Any]:
    """Back-compat: dict-of-dict input → dict-of-dict merged output (prefer_target)."""
    return merge_ir(source_state, target_state, strategy="prefer_target")
