from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models import DecisionRecord
from backend.app.evaluation import utils as eval_utils


def _make_database_url(db_path: str | Path) -> str:
    resolved = Path(db_path).expanduser().resolve()
    return f"sqlite+aiosqlite:///{resolved.as_posix()}"


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    trimmed = value.strip()
    if trimmed.endswith("Z"):
        trimmed = trimmed[:-1]
    if not trimmed:
        return None
    return datetime.fromisoformat(trimmed)


async def fetch_decisions(
    *,
    db_path: str | Path,
    start: datetime | None = None,
    end: datetime | None = None,
    validated_only: bool = False,
) -> List[DecisionRecord]:
    engine = create_async_engine(_make_database_url(db_path), future=True)
    session_factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            stmt = select(DecisionRecord)
            if start:
                stmt = stmt.where(DecisionRecord.timestamp >= start)
            if end:
                stmt = stmt.where(DecisionRecord.timestamp <= end)
            stmt = stmt.order_by(DecisionRecord.timestamp.asc())
            result = await session.exec(stmt)
            records: Sequence[DecisionRecord] = result.all()
        if validated_only:
            filtered = [r for r in records if eval_utils.decision_correctness(r) is not None]
        else:
            filtered = list(records)
        return list(filtered)
    finally:
        await engine.dispose()


def run_async(func, *args, **kwargs):  # noqa: ANN001
    return asyncio.run(func(*args, **kwargs))
