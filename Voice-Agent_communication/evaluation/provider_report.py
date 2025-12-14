from __future__ import annotations

import argparse
from pathlib import Path

from backend.app.evaluation import provider_report as provider_core

from ._common import fetch_decisions, parse_datetime, run_async


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Provider/model comparison over ledger slice")
    parser.add_argument("--db", required=True, help="Path to decision_ledger SQLite database")
    parser.add_argument("--start", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--end", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--validated-only", action="store_true", help="Restrict to validated samples")
    parser.add_argument(
        "--export",
        type=Path,
        default=None,
        help="Optional CSV export destination",
    )
    return parser


def render_table(metrics):  # noqa: ANN001
    header = [
        "provider",
        "model",
        "total",
        "mean_confidence",
        "block_rate",
        "false_allow_rate",
        "false_block_rate",
        "accuracy",
    ]
    print(",".join(header))
    for entry in metrics:
        print(
            f"{entry.provider},{entry.model},{entry.total},{entry.mean_confidence},"
            f"{entry.block_rate},{entry.false_allow_rate},{entry.false_block_rate},{entry.accuracy}"
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

    metrics = provider_core.build_provider_report(records)

    if args.export:
        csv_payload = provider_core.render_report_csv(metrics)
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_text(csv_payload, encoding="utf-8")
        print(f"exported={args.export.as_posix()}")
    else:
        render_table(metrics)


if __name__ == "__main__":
    main()
