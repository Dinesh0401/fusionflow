from __future__ import annotations

import argparse

from backend.app.evaluation import calibration as calibration_core

from ._common import fetch_decisions, parse_datetime, run_async


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Calibration metrics over ledger slice")
    parser.add_argument("--db", required=True, help="Path to decision_ledger SQLite database")
    parser.add_argument("--start", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--end", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--validated-only", action="store_true", help="Restrict to validated samples")
    parser.add_argument("--bins", type=int, default=10, help="Number of calibration buckets")
    return parser


def render(metrics: calibration_core.CalibrationMetrics) -> None:
    print(f"total_evaluated={metrics.total_evaluated}")
    print(f"expected_calibration_error={metrics.expected_calibration_error}")
    print(f"overconfidence_rate={metrics.overconfidence_rate}")
    print(f"underconfidence_rate={metrics.underconfidence_rate}")
    print("bin_lower,bin_upper,count,avg_confidence,empirical_accuracy")
    for bin_metric in metrics.bins:
        print(
            f"{bin_metric.lower_bound:.2f},{bin_metric.upper_bound:.2f},{bin_metric.count},"
            f"{bin_metric.avg_confidence:.6f},{bin_metric.empirical_accuracy:.6f}"
        )


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
        validated_only=args.validated_only,
    )

    metrics = calibration_core.expected_calibration_error(records, bins=args.bins)
    render(metrics)


if __name__ == "__main__":
    main()
