from datetime import datetime
from typing import Iterable, List

from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import DecisionRecord


class LedgerReader:
    """Helper for querying decision records for offline evaluation."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def fetch_decisions(
        self,
        *,
        since: datetime | None = None,
        provider: str | None = None,
        model: str | None = None,
        limit: int | None = None,
    ) -> List[DecisionRecord]:
        stmt = select(DecisionRecord).order_by(DecisionRecord.timestamp.desc())
        if since:
            stmt = stmt.where(DecisionRecord.timestamp >= since)
        if provider:
            stmt = stmt.where(DecisionRecord.provider == provider)
        if model:
            stmt = stmt.where(DecisionRecord.model == model)
        if limit:
            stmt = stmt.limit(limit)

        async with self._session_factory() as session:
            result = await session.exec(stmt)
            return list(result.all())

    async def iter_by_prompt_hash(
        self,
        *,
        prompt_hash: str,
        provider: str | None = None,
    ) -> Iterable[DecisionRecord]:
        stmt = select(DecisionRecord).where(DecisionRecord.prompt_hash == prompt_hash)
        if provider:
            stmt = stmt.where(DecisionRecord.provider == provider)

        async with self._session_factory() as session:
            result = await session.exec(stmt)
            for record in result:
                yield record
