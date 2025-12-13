"""Configuration management for the NeuroAdaptive ETL Orchestration Platform.

The platform intentionally keeps configuration small and explicit so that it can be
extended by environment variables without requiring a separate configuration file.
"""

import os
from dataclasses import dataclass
from typing import Literal

Environment = Literal["development", "testing", "production"]


@dataclass
class Settings:
    """Strongly-typed settings object consumed across the platform."""

    env: Environment = "development"
    log_level: str = "INFO"
    database_uri: str = "sqlite:///:memory:"
    warehouse_uri: str = "warehouse://local/mock"
    metrics_enabled: bool = True
    alerts_enabled: bool = True
    scheduler_tick_seconds: float = 1.0
    max_retries: int = 1
    retry_delay_seconds: float = 0.5
    use_mock_data: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        env: Environment = os.getenv("NAEOP_ENV", "development").lower()  # type: ignore[assignment]
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        database_uri = os.getenv(
            "DATABASE_URI",
            os.getenv("DEV_DATABASE_URI", "sqlite:///:memory:"),
        )
        warehouse_uri = os.getenv("WAREHOUSE_URI", "warehouse://local/mock")

        if env == "production":
            database_uri = os.getenv(
                "PROD_DATABASE_URI",
                os.getenv("DATABASE_URI", "postgresql://prod_user:prod_password@localhost:5432/prod_dbname"),
            )
            warehouse_uri = os.getenv("PROD_WAREHOUSE_URI", warehouse_uri)
        elif env == "testing":
            database_uri = os.getenv(
                "TEST_DATABASE_URI",
                "sqlite:///:memory:",
            )

        return cls(
            env=env,
            log_level=log_level,
            database_uri=database_uri,
            warehouse_uri=warehouse_uri,
            metrics_enabled=os.getenv("METRICS_ENABLED", "True").lower() == "true",
            alerts_enabled=os.getenv("ALERTS_ENABLED", "True").lower() == "true",
            scheduler_tick_seconds=float(os.getenv("SCHEDULER_TICK_SECONDS", "1")),
            max_retries=int(os.getenv("MAX_RETRIES", "1")),
            retry_delay_seconds=float(os.getenv("RETRY_DELAY_SECONDS", "0.5")),
            use_mock_data=os.getenv("USE_MOCK_DATA", "True").lower() == "true",
        )


def get_settings() -> Settings:
    """Return a cached settings instance so downstream callers share configuration."""

    global _CACHED_SETTINGS  # type: ignore
    try:
        return _CACHED_SETTINGS  # type: ignore
    except NameError:
        _CACHED_SETTINGS = Settings.from_env()  # type: ignore
        return _CACHED_SETTINGS  # type: ignore