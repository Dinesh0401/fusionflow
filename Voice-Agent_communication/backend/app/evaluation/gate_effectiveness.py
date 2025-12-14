from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import DecisionRecord


@dataclass(slots=True)
class GateEffectiveness:
    total_blocks: int
    evaluated_blocks: int
    precision: float
    recall: float
    false_block_cost: int
    false_allow_cost: int
    notes: str | None = None


def analyze_gate_effectiveness(decisions: Iterable[DecisionRecord]) -> GateEffectiveness:
    total_blocks = 0
    evaluated_blocks = 0
    true_positive_blocks = 0
    false_positive_blocks = 0

    total_harmful = 0
    false_allows = 0

    for record in decisions:
        verdict = (record.gate_verdict or "").lower()
        if verdict == "block":
            total_blocks += 1
            if record.downstream_failure is None:
                continue
            evaluated_blocks += 1
            if record.downstream_failure:
                true_positive_blocks += 1
            else:
                false_positive_blocks += 1
        elif verdict == "allow":
            if record.downstream_failure is None:
                continue
            if record.downstream_failure:
                false_allows += 1
            total_harmful += 1  # counts harmful automations encountered

    precision = (
        true_positive_blocks / (true_positive_blocks + false_positive_blocks)
        if (true_positive_blocks + false_positive_blocks) > 0
        else 0.0
    )
    recall = (
        true_positive_blocks / (true_positive_blocks + false_allows)
        if (true_positive_blocks + false_allows) > 0
        else 0.0
    )

    notes = None
    if evaluated_blocks == 0:
        notes = "Insufficient annotated block decisions to compute precision."

    return GateEffectiveness(
        total_blocks=total_blocks,
        evaluated_blocks=evaluated_blocks,
        precision=round(precision, 6),
        recall=round(recall, 6),
        false_block_cost=false_positive_blocks,
        false_allow_cost=false_allows,
        notes=notes,
    )
