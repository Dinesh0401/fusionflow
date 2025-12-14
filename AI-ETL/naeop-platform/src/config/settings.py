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
    telemetry_path: str = "data/telemetry/pipeline_runs.csv"
    failure_model_path: str = "models/failure_model.joblib"
    failure_risk_threshold: float = 0.6
    use_advanced_failure_model: bool = True
    advanced_failure_model_path: str = "models/failure_model_advanced.joblib"
    failure_risk_ensemble_weight: float = 0.6
    llm_agent_enabled: bool = True
    llm_agent_provider: str = "mock"
    llm_agent_model: str = "gpt-4o-mini"
    llm_agent_temperature: float = 0.2
    llm_agent_max_tokens: int = 512
    llm_agent_api_key_env: str = "OPENAI_API_KEY"
    llm_agent_endpoint: str = ""
    llm_agent_decision_threshold: float = 0.6
    llm_agent_human_in_loop: bool = True

    # Alert backend settings
    alert_backend: str = "stdout"  # stdout | slack | email
    slack_webhook_url: str = ""
    slack_timeout_seconds: float = 5.0
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_smtp_username: str = ""
    email_smtp_password: str = ""
    email_recipients: str = ""  # comma-separated

    # Retry policy settings
    retry_strategy: str = "fixed"  # fixed | exponential
    retry_base_delay_seconds: float = 1.0
    retry_max_delay_seconds: float = 30.0
    retry_jitter: float = 0.25

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
            telemetry_path=os.getenv("TELEMETRY_PATH", "data/telemetry/pipeline_runs.csv"),
            failure_model_path=os.getenv("FAILURE_MODEL_PATH", "models/failure_model.joblib"),
            failure_risk_threshold=float(os.getenv("FAILURE_RISK_THRESHOLD", "0.6")),
            use_advanced_failure_model=os.getenv("USE_ADVANCED_FAILURE_MODEL", "True").lower() == "true",
            advanced_failure_model_path=os.getenv("ADVANCED_FAILURE_MODEL_PATH", "models/failure_model_advanced.joblib"),
            failure_risk_ensemble_weight=float(os.getenv("FAILURE_RISK_ENSEMBLE_WEIGHT", "0.6")),
            llm_agent_enabled=os.getenv("LLM_AGENT_ENABLED", "True").lower() == "true",
            llm_agent_provider=os.getenv("LLM_AGENT_PROVIDER", "mock"),
            llm_agent_model=os.getenv("LLM_AGENT_MODEL", "gpt-4o-mini"),
            llm_agent_temperature=float(os.getenv("LLM_AGENT_TEMPERATURE", "0.2")),
            llm_agent_max_tokens=int(os.getenv("LLM_AGENT_MAX_TOKENS", "512")),
            llm_agent_api_key_env=os.getenv("LLM_AGENT_API_KEY_ENV", "OPENAI_API_KEY"),
            llm_agent_endpoint=os.getenv("LLM_AGENT_ENDPOINT", ""),
            llm_agent_decision_threshold=float(os.getenv("LLM_AGENT_DECISION_THRESHOLD", "0.6")),
            llm_agent_human_in_loop=os.getenv("LLM_AGENT_HUMAN_IN_LOOP", "True").lower() == "true",
            alert_backend=os.getenv("ALERT_BACKEND", "stdout"),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            slack_timeout_seconds=float(os.getenv("SLACK_TIMEOUT_SECONDS", "5.0")),
            email_smtp_host=os.getenv("EMAIL_SMTP_HOST", ""),
            email_smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
            email_smtp_username=os.getenv("EMAIL_SMTP_USERNAME", ""),
            email_smtp_password=os.getenv("EMAIL_SMTP_PASSWORD", ""),
            email_recipients=os.getenv("EMAIL_RECIPIENTS", ""),
            retry_strategy=os.getenv("RETRY_STRATEGY", "fixed"),
            retry_base_delay_seconds=float(os.getenv("RETRY_BASE_DELAY_SECONDS", "1.0")),
            retry_max_delay_seconds=float(os.getenv("RETRY_MAX_DELAY_SECONDS", "30.0")),
            retry_jitter=float(os.getenv("RETRY_JITTER", "0.25")),
        )


def get_settings() -> Settings:
    """Return a cached settings instance so downstream callers share configuration."""

    global _CACHED_SETTINGS  # type: ignore
    try:
        return _CACHED_SETTINGS  # type: ignore
    except NameError:
        _CACHED_SETTINGS = Settings.from_env()  # type: ignore
        return _CACHED_SETTINGS  # type: ignore