from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "VocaVerse API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me"  # TODO: replace with secure secret
    access_token_expire_minutes: int = 60

    # MCP configuration
    mcp_server_url: str = "http://localhost:8400"
    mcp_api_key: str | None = None

    # Database configuration
    database_url: str = "sqlite+aiosqlite:///./data/vocaverse.db"

    # Decision gate thresholds
    ml_risk_threshold: float = 0.7
    llm_confidence_threshold: float = 0.6
    blocked_providers: list[str] = Field(default_factory=list)
    blocked_models: list[str] = Field(default_factory=list)

    # Telemetry
    otel_exporter_endpoint: str | None = None
    otel_exporter_headers: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    @field_validator("blocked_providers", "blocked_models", mode="before")
    @classmethod
    def _normalize_list(cls, value):
        if isinstance(value, str):
            if not value.strip():
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
