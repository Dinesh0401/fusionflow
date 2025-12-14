from __future__ import annotations

import csv
import io
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List

from ..models import DecisionRecord
from .utils import decision_correctness, is_false_allow, is_false_block


@dataclass(slots=True)
class ProviderMetrics:
    provider: str
    model: str
    total: int
    mean_confidence: float
    block_rate: float
    false_allow_rate: float
    false_block_rate: float
    accuracy: float


def build_provider_report(decisions: Iterable[DecisionRecord]) -> List[ProviderMetrics]:
    groups: Dict[tuple[str, str], List[DecisionRecord]] = defaultdict(list)
    for decision in decisions:
        groups[(decision.provider, decision.model)].append(decision)

    metrics: List[ProviderMetrics] = []
    for (provider, model), records in sorted(groups.items()):
        total = len(records)
        if total == 0:
            continue

        confidence_values = [r.llm_confidence for r in records if r.llm_confidence is not None]
        mean_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0

        block_count = sum(1 for r in records if (r.gate_verdict or "").lower() == "block")
        allows = total - block_count

        false_allows = sum(1 for r in records if is_false_allow(r))
        false_blocks = sum(1 for r in records if is_false_block(r))

        correctness = [decision_correctness(r) for r in records]
        known_correctness = [value for value in correctness if value is not None]
        accuracy = sum(1 for value in known_correctness if value) / len(known_correctness) if known_correctness else 0.0

        metrics.append(
            ProviderMetrics(
                provider=provider,
                model=model,
                total=total,
                mean_confidence=round(mean_confidence, 6),
                block_rate=round(block_count / total, 6),
                false_allow_rate=round(false_allows / total, 6) if total else 0.0,
                false_block_rate=round(false_blocks / total, 6) if total else 0.0,
                accuracy=round(accuracy, 6),
            )
        )

    return metrics


def render_report_csv(metrics: Iterable[ProviderMetrics]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "provider",
            "model",
            "total",
            "mean_confidence",
            "block_rate",
            "false_allow_rate",
            "false_block_rate",
            "accuracy",
        ]
    )
    for metric in metrics:
        writer.writerow(
            [
                metric.provider,
                metric.model,
                metric.total,
                metric.mean_confidence,
                metric.block_rate,
                metric.false_allow_rate,
                metric.false_block_rate,
                metric.accuracy,
            ]
        )
    return buffer.getvalue()


def render_report_json(metrics: Iterable[ProviderMetrics]) -> List[dict[str, object]]:
    return [
        {
            "provider": metric.provider,
            "model": metric.model,
            "total": metric.total,
            "mean_confidence": metric.mean_confidence,
            "block_rate": metric.block_rate,
            "false_allow_rate": metric.false_allow_rate,
            "false_block_rate": metric.false_block_rate,
            "accuracy": metric.accuracy,
        }
        for metric in metrics
    ]
