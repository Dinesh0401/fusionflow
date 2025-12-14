from __future__ import annotations

import argparse
from collections import defaultdict
from operator import itemgetter
from typing import Dict, Iterable, List, Tuple

from backend.app.models import DecisionRecord

from .._common import fetch_decisions, parse_datetime, run_async

DEFAULT_CONFIDENCE_DRIFT = 0.2
DEFAULT_LIMIT = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Prompt hash regression scan")
    parser.add_argument("--db", required=True, help="Path to decision_ledger SQLite database")
    parser.add_argument("--start", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--end", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument(
        "--confidence-drift-threshold",
        type=float,
        default=DEFAULT_CONFIDENCE_DRIFT,
        help="Minimum confidence delta to flag",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Maximum rows to print per category",
    )
    return parser


def group_by_prompt_hash(records: Iterable[DecisionRecord]) -> Dict[str, List[DecisionRecord]]:
    buckets: Dict[str, List[DecisionRecord]] = defaultdict(list)
    for record in records:
        buckets[record.prompt_hash].append(record)
    return buckets


def detect_mixed_verdicts(bucket: List[DecisionRecord]) -> bool:
    verdicts = {normalize_verdict(r.gate_verdict) for r in bucket if r.gate_verdict}
    return len(verdicts) > 1


def normalize_verdict(value: str | None) -> str:
    return (value or "").strip().lower()


def detect_confidence_drift(bucket: List[DecisionRecord], threshold: float) -> float:
    confidences = [float(r.llm_confidence) for r in bucket if r.llm_confidence is not None]
    if len(confidences) < 2:
        return 0.0
    drift = max(confidences) - min(confidences)
    return drift if drift >= threshold else 0.0


def detect_provider_divergence(bucket: List[DecisionRecord]) -> bool:
    provider_verdicts: Dict[str, set[str]] = defaultdict(set)
    for record in bucket:
        verdict = normalize_verdict(record.gate_verdict)
        provider_verdicts[record.provider].add(verdict)
    verdict_sets = {frozenset(verdicts) for verdicts in provider_verdicts.values() if verdicts}
    return len(provider_verdicts) > 1 and len(verdict_sets) > 1


def render_report(
    *,
    grouped: Dict[str, List[DecisionRecord]],
    drift_threshold: float,
    limit: int,
) -> None:
    mixed: List[Tuple[str, int]] = []
    drift: List[Tuple[str, float, int]] = []
    divergence: List[Tuple[str, Dict[str, List[str]]]] = []

    for prompt_hash, bucket in grouped.items():
        if detect_mixed_verdicts(bucket):
            mixed.append((prompt_hash, len(bucket)))
        drift_value = detect_confidence_drift(bucket, drift_threshold)
        if drift_value:
            drift.append((prompt_hash, round(drift_value, 6), len(bucket)))
        if detect_provider_divergence(bucket):
            provider_summary: Dict[str, List[str]] = defaultdict(list)
            for record in bucket:
                provider_summary[record.provider].append(normalize_verdict(record.gate_verdict))
            divergence.append((prompt_hash, provider_summary))

    print(f"prompt_hashes_total={len(grouped)}")
    print(f"mixed_verdict_hashes={len(mixed)}")
    print(f"confidence_drift_hashes={len(drift)}")
    print(f"provider_divergence_hashes={len(divergence)}")

    if mixed:
        print("-- mixed_verdict_samples --")
        for prompt_hash, count in sorted(mixed, key=itemgetter(1), reverse=True)[:limit]:
            print(f"prompt_hash={prompt_hash} count={count}")

    if drift:
        print("-- confidence_drift_samples --")
        for prompt_hash, delta, count in sorted(drift, key=itemgetter(1), reverse=True)[:limit]:
            print(f"prompt_hash={prompt_hash} delta={delta} count={count}")

    if divergence:
        print("-- provider_divergence_samples --")
        for prompt_hash, provider_summary in divergence[:limit]:
            flattened = "; ".join(
                f"{provider}:{','.join(sorted(set(verdicts)))}" for provider, verdicts in sorted(provider_summary.items())
            )
            print(f"prompt_hash={prompt_hash} providers={flattened}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    start = parse_datetime(args.start)
    end = parse_datetime(args.end)

    records = run_async(
        fetch_decisions,
        db_path=args.db,
        start=start,
        end=end,
        validated_only=False,
    )

    grouped = group_by_prompt_hash(records)
    render_report(grouped=grouped, drift_threshold=args.confidence_drift_threshold, limit=args.limit)


if __name__ == "__main__":
    main()
