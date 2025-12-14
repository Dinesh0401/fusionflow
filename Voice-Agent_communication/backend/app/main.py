from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .core.config import get_settings
from .core.db import get_async_engine
from .core.telemetry import setup_telemetry
from .services.decision_ledger import DecisionLedger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry(
        service_name=settings.app_name,
        exporter_endpoint=settings.otel_exporter_endpoint,
        exporter_headers=settings.otel_exporter_headers,
    )
    engine = get_async_engine(settings.database_url)
    ledger = DecisionLedger(engine)
    await ledger.init_db()
    app.state.db_engine = engine
    app.state.decision_ledger = ledger
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(title=settings.app_name, openapi_url=f"{settings.api_v1_prefix}/openapi.json", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
