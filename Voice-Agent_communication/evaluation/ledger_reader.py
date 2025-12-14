from __future__ import annotations

import argparse
from collections import Counter
from typing import Iterable

from backend.app.evaluation import utils as eval_utils

from ._common import fetch_decisions, parse_datetime, run_async


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Ledger window inspection")
    parser.add_argument("--db", required=True, help="Path to decision_ledger SQLite database")
    parser.add_argument("--start", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument("--end", required=False, help="Inclusive ISO timestamp filter (UTC)")
    parser.add_argument(
        "--validated-only",
        action="store_true",
        help="Restrict summary to decisions with downstream validation",
    )
    return parser


def summarize(records: Iterable) -> None:  # noqa: ANN401
    total = len(records)
    if total == 0:
        print("records_total=0")
        return

    timestamps = [r.timestamp for r in records]
    validated = [r for r in records if eval_utils.decision_correctness(r) is not None]
    providers = Counter((r.provider, r.model) for r in records)

    print(f"records_total={total}")
    print(f"records_validated={len(validated)}")
    print(f"records_unvalidated={total - len(validated)}")
    print(f"window_start={min(timestamps).isoformat()}" )
    print(f"window_end={max(timestamps).isoformat()}")
    for (provider, model), count in providers.most_common():
        print(f"provider={provider} model={model} count={count}")


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

    summarize(records)


if __name__ == "__main__":
    main()
