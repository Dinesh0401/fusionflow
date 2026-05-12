"""IR-aware semantic diff for FusionFlow specifications.

Compares two Temporal IR dicts produced by ir_export.build_temporal_ir and
classifies the differences as added / removed / changed per top-level section
(datasets, pipelines, models, experiments, timelines, merges).

Used by:
- `fusionflow diff a.ff b.ff` CLI subcommand (v0.5+)
- merge_algorithm conflict detection (v0.5+)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChangeDetail:
    """The before/after view of a single keyed entry plus the list of field
    paths that differ between them."""

    before: Dict[str, Any]
    after: Dict[str, Any]
    field_changes: List[str] = field(default_factory=list)


@dataclass
class SectionDiff:
    """Diff of one top-level IR section (datasets, pipelines, models, ...).

    The section is treated as a dict[key -> entry]. Keys in `added` exist only
    in B; keys in `removed` exist only in A; `changed` maps shared keys to a
    ChangeDetail describing the before/after content.
    """

    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: Dict[str, ChangeDetail] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.added and not self.removed and not self.changed


@dataclass
class MergesDiff:
    """Diff of the top-level merges list (which is order-sensitive but not keyed)."""

    added: List[Dict[str, Any]] = field(default_factory=list)
    removed: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.added and not self.removed


@dataclass
class IRDiff:
    """The complete diff between two IR dicts."""

    ir_version_before: str
    ir_version_after: str
    datasets: SectionDiff = field(default_factory=SectionDiff)
    pipelines: SectionDiff = field(default_factory=SectionDiff)
    models: SectionDiff = field(default_factory=SectionDiff)
    experiments: SectionDiff = field(default_factory=SectionDiff)
    timelines: SectionDiff = field(default_factory=SectionDiff)
    merges: MergesDiff = field(default_factory=MergesDiff)

    @property
    def is_empty(self) -> bool:
        """True iff the two IRs are structurally identical."""
        return (
            self.datasets.is_empty
            and self.pipelines.is_empty
            and self.models.is_empty
            and self.experiments.is_empty
            and self.timelines.is_empty
            and self.merges.is_empty
            and self.ir_version_before == self.ir_version_after
        )


_KEYED_SECTIONS = ("datasets", "pipelines", "models", "experiments", "timelines")


def _diff_section(before: Dict[str, Any], after: Dict[str, Any]) -> SectionDiff:
    """Diff one top-level keyed section. Returns added / removed / changed."""
    diff = SectionDiff()
    before_keys = set(before.keys())
    after_keys = set(after.keys())

    diff.removed = sorted(before_keys - after_keys)
    diff.added = sorted(after_keys - before_keys)

    for key in sorted(before_keys & after_keys):
        b = before[key]
        a = after[key]
        if b != a:
            diff.changed[key] = ChangeDetail(
                before=b,
                after=a,
                field_changes=_field_changes(b, a),
            )
    return diff


def _field_changes(before: Any, after: Any, prefix: str = "") -> List[str]:
    """Walk two nested dicts and return a list of dotted paths where they differ."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        if before != after:
            return [prefix or "."]
        return []

    paths: List[str] = []
    all_keys = sorted(set(before.keys()) | set(after.keys()))
    for key in all_keys:
        sub_prefix = f"{prefix}.{key}" if prefix else key
        if key not in before:
            paths.append(f"{sub_prefix} (added)")
        elif key not in after:
            paths.append(f"{sub_prefix} (removed)")
        else:
            paths.extend(_field_changes(before[key], after[key], sub_prefix))
    return paths


def _diff_merges(before: List[Dict[str, Any]], after: List[Dict[str, Any]]) -> MergesDiff:
    """Treat the merges list as a multiset; report items present on only one side."""
    diff = MergesDiff()
    # Use stable string representation for membership checks (dicts aren't hashable).
    before_keys = [json.dumps(m, sort_keys=True) for m in before]
    after_keys = [json.dumps(m, sort_keys=True) for m in after]
    before_only = list(before_keys)
    after_only = list(after_keys)
    for k in list(before_only):
        if k in after_only:
            before_only.remove(k)
            after_only.remove(k)
    diff.removed = [json.loads(k) for k in before_only]
    diff.added = [json.loads(k) for k in after_only]
    return diff


def diff_ir(before: Dict[str, Any], after: Dict[str, Any]) -> IRDiff:
    """Produce a structured diff between two FusionFlow IR dicts."""
    return IRDiff(
        ir_version_before=before.get("ir_version", "0.3"),
        ir_version_after=after.get("ir_version", "0.3"),
        datasets=_diff_section(before.get("datasets", {}), after.get("datasets", {})),
        pipelines=_diff_section(before.get("pipelines", {}), after.get("pipelines", {})),
        models=_diff_section(before.get("models", {}), after.get("models", {})),
        experiments=_diff_section(before.get("experiments", {}), after.get("experiments", {})),
        timelines=_diff_section(before.get("timelines", {}), after.get("timelines", {})),
        merges=_diff_merges(before.get("merges", []), after.get("merges", [])),
    )


def format_diff_human(diff: IRDiff) -> str:
    """Render an IRDiff as a human-readable string for terminal output."""
    if diff.is_empty:
        return "Identical: both IRs are byte-equivalent at the structural level."

    lines: List[str] = []
    if diff.ir_version_before != diff.ir_version_after:
        lines.append(f"ir_version: {diff.ir_version_before} -> {diff.ir_version_after}")
        lines.append("")

    for section_name in _KEYED_SECTIONS:
        section: SectionDiff = getattr(diff, section_name)
        if section.is_empty:
            continue
        lines.append(f"{section_name}:")
        for key in section.added:
            lines.append(f"  + {key}")
        for key in section.removed:
            lines.append(f"  - {key}")
        for key, detail in section.changed.items():
            lines.append(f"  ~ {key}")
            for path in detail.field_changes:
                lines.append(f"      {path}")
        lines.append("")

    if not diff.merges.is_empty:
        lines.append("merges:")
        for merge in diff.merges.added:
            lines.append(f"  + {merge.get('source')} -> {merge.get('target')}")
        for merge in diff.merges.removed:
            lines.append(f"  - {merge.get('source')} -> {merge.get('target')}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def format_diff_json(diff: IRDiff) -> str:
    """Render an IRDiff as JSON (for machine consumers / CI)."""

    def section_to_dict(section: SectionDiff) -> Dict[str, Any]:
        return {
            "added": list(section.added),
            "removed": list(section.removed),
            "changed": {
                key: {
                    "before": detail.before,
                    "after": detail.after,
                    "field_changes": list(detail.field_changes),
                }
                for key, detail in section.changed.items()
            },
        }

    payload = {
        "ir_version_before": diff.ir_version_before,
        "ir_version_after": diff.ir_version_after,
        "datasets": section_to_dict(diff.datasets),
        "pipelines": section_to_dict(diff.pipelines),
        "models": section_to_dict(diff.models),
        "experiments": section_to_dict(diff.experiments),
        "timelines": section_to_dict(diff.timelines),
        "merges": {
            "added": list(diff.merges.added),
            "removed": list(diff.merges.removed),
        },
    }
    return json.dumps(payload, indent=2, sort_keys=False)
