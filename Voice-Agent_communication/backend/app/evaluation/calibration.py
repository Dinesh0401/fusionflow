from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..models import DecisionRecord
from .utils import decision_correctness


@dataclass(slots=True)
class CalibrationBin:
    lower_bound: float
    upper_bound: float
    count: int
    avg_confidence: float
    empirical_accuracy: float


@dataclass(slots=True)
class CalibrationMetrics:
    total_evaluated: int
    expected_calibration_error: float
    overconfidence_rate: float
    underconfidence_rate: float
    bins: List[CalibrationBin]


def _iter_calibration_samples(decisions: Iterable[DecisionRecord]):
    for record in decisions:
        correctness = decision_correctness(record)
        confidence = record.llm_confidence
        if correctness is None or confidence is None:
            continue
        yield float(confidence), 1.0 if correctness else 0.0


def expected_calibration_error(decisions: Iterable[DecisionRecord], bins: int = 10) -> CalibrationMetrics:
    bucket_totals = [0.0 for _ in range(bins)]
    bucket_correct = [0.0 for _ in range(bins)]
    bucket_confidence = [0.0 for _ in range(bins)]

    samples = list(_iter_calibration_samples(decisions))
    if not samples:
        return CalibrationMetrics(
            total_evaluated=0,
            expected_calibration_error=0.0,
            overconfidence_rate=0.0,
            underconfidence_rate=0.0,
            bins=[
                CalibrationBin(
                    lower_bound=i / bins,
                    upper_bound=(i + 1) / bins,
                    count=0,
                    avg_confidence=0.0,
                    empirical_accuracy=0.0,
                )
                for i in range(bins)
            ],
        )

    total = len(samples)
    overconfident = 0
    underconfident = 0

    for confidence, correctness in samples:
        idx = min(bins - 1, int(confidence * bins))
        bucket_totals[idx] += 1
        bucket_correct[idx] += correctness
        bucket_confidence[idx] += confidence

        if correctness == 0.0 and confidence >= 0.5:
            overconfident += 1
        elif correctness == 1.0 and confidence <= 0.5:
            underconfident += 1

    ece = 0.0
    bin_stats: List[CalibrationBin] = []

    for i in range(bins):
        count = bucket_totals[i]
        if count > 0:
            avg_conf = bucket_confidence[i] / count
            acc = bucket_correct[i] / count
            ece += abs(acc - avg_conf) * (count / total)
        else:
            avg_conf = 0.0
            acc = 0.0
        bin_stats.append(
            CalibrationBin(
                lower_bound=i / bins,
                upper_bound=(i + 1) / bins,
                count=int(count),
                avg_confidence=avg_conf,
                empirical_accuracy=acc,
            )
        )

    return CalibrationMetrics(
        total_evaluated=total,
        expected_calibration_error=round(ece, 6),
        overconfidence_rate=round(overconfident / total, 6),
        underconfidence_rate=round(underconfident / total, 6),
        bins=bin_stats,
    )
