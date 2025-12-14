from __future__ import annotations

import argparse

from backend.app.evaluation import gate_effectiveness as gate_core

from ._common import fetch_decisions, parse_datetime, run_async


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Gate effectiveness metrics over ledger slice")
    parser.add_argument("--db", required=True, help="Path to decision_ledger SQLite database")
    parser.add_argument("--start", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--end", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--validated-only", action="store_true", help="Restrict to validated samples")
    return parser


def render(metrics: gate_core.GateEffectiveness) -> None:
    print(f"total_blocks={metrics.total_blocks}")
    print(f"evaluated_blocks={metrics.evaluated_blocks}")
    print(f"precision={metrics.precision}")
    print(f"recall={metrics.recall}")
    print(f"false_block_cost={metrics.false_block_cost}")
    print(f"false_allow_cost={metrics.false_allow_cost}")
    if metrics.notes:
        print(f"notes={metrics.notes}")


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

    metrics = gate_core.analyze_gate_effectiveness(records)
    render(metrics)


if __name__ == "__main__":
    main()
