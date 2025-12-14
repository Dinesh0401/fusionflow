import argparse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.config import get_settings
from ..core.db import get_async_engine
from ..evaluation.ledger_reader import LedgerReader
from ..evaluation.provider_report import build_provider_report, render_report_csv, render_report_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export provider-level decision metrics.")
    parser.add_argument("--since-days", type=int, default=None, help="Restrict to decisions since N days ago.")
    parser.add_argument("--provider", type=str, default=None, help="Filter by provider identifier.")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", type=Path, default=None, help="Optional output file path. Defaults to stdout.")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    engine = get_async_engine(settings.database_url)
    session_factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    reader = LedgerReader(session_factory)

    since = datetime.utcnow() - timedelta(days=args.since_days) if args.since_days else None

    decisions = await reader.fetch_decisions(since=since, provider=args.provider)
    metrics = build_provider_report(decisions)

    if args.format == "csv":
        payload = render_report_csv(metrics)
    else:
        payload = json_dumps(render_report_json(metrics))

    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)

    await engine.dispose()


def json_dumps(payload):
    import json

    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
