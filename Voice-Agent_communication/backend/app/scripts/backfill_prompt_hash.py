import asyncio

from ..core.config import get_settings
from ..core.db import get_async_engine
from ..services.decision_ledger import DecisionLedger


async def main() -> None:
    settings = get_settings()
    engine = get_async_engine(settings.database_url)
    ledger = DecisionLedger(engine)
    updated = await ledger.backfill_prompt_hash()
    await engine.dispose()
    print(f"Updated {updated} decision records with fallback prompt hash")


if __name__ == "__main__":
    asyncio.run(main())
