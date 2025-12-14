from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def _make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, future=True)


@lru_cache
def get_async_engine(database_url: str) -> AsyncEngine:
    """Return a cached async engine for the provided database URL."""
    return _make_engine(database_url)
