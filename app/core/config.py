"""Centralized configuration. Everything defaults to safe, local, offline behavior."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # --- General ---
    app_name: str = "azure-devops-operations-poc"
    environment: str = "local"
    log_level: str = "INFO"

    # --- Persistence ---
    # "sqlite:///./data/app.db" for a file, or "sqlite://:memory:" for tests.
    database_path: str = "./data/app.db"

    # --- Rule engine thresholds (all configurable, none hardcoded in logic) ---
    restart_count_threshold: int = 3
    error_rate_threshold: float = 0.05  # 5%
    latency_threshold_ms: float = 1000.0
    node_ready_ratio_threshold: float = 0.7  # below this ratio of ready nodes triggers a warning

    score_deployment_failed: int = 40
    score_pod_restart: int = 25
    score_readiness_failure: int = 20
    score_high_error_rate: int = 25
    score_high_latency: int = 20
    score_node_warning: int = 15
    score_compound_warning_bonus: int = 10

    severity_critical_threshold: int = 70
    severity_high_threshold: int = 40
    severity_warning_threshold: int = 15

    # --- Optional AI incident assistant (advisory only, never executes actions) ---
    # "deterministic" (default, offline) or "azure_openai" (illustrative only).
    ai_provider: str = "deterministic"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_timeout_seconds: float = 5.0


def get_settings() -> Settings:
    return Settings()
