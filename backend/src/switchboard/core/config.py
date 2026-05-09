from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from switchboard.core.constants import (
    DEFAULT_GEMINI_LANGUAGE,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GEMINI_VOICE,
    DEFAULT_SMS_SENDER_ID,
)
from switchboard.models.enums import (
    AuthMode,
    Environment,
    GeminiProvider,
    LogLevel,
    StorageMode,
    ToolDispatchMode,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", REPO_ROOT / ".env.local"),
        env_file_encoding="utf-8",
        env_prefix="SWITCHBOARD_",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- environment ----
    env: Environment = Environment.DEV
    version: str = "0.1.0"
    region: str = "europe-west4"

    # ---- HTTP server ----
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")

    # ---- database ----
    database_url: str = f"sqlite:///{REPO_ROOT / 'backend' / 'switchboard.db'}"
    seed_dev_data: bool = True
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10

    # ---- logging ----
    log_level: LogLevel = LogLevel.INFO
    log_json: bool = False

    # ---- realtime bridge ↔ application backend (PRD §8.2 / §8.10) ----
    tool_dispatch_mode: ToolDispatchMode = ToolDispatchMode.LOCAL
    application_backend_url: str = "http://127.0.0.1:8000"
    bridge_internal_token: str = ""

    # ---- gemini live ----
    gemini_provider: GeminiProvider = GeminiProvider.API_KEY
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = DEFAULT_GEMINI_MODEL
    gemini_voice: str = DEFAULT_GEMINI_VOICE
    gemini_language: str = DEFAULT_GEMINI_LANGUAGE
    vertex_project: str = ""
    vertex_location: str = "europe-west4"

    # ---- google cloud ----
    gcp_project: str = ""
    gcs_bucket_prefix: str = "switchboard-rec"
    gcs_recording_retention_days: int = 7
    kms_keyring: str = "switchboard"
    kms_location: str = "europe-west4"

    storage_mode: StorageMode = StorageMode.LOCAL

    # ---- redis (optional, deferred — Memorystore in prod) ----
    redis_url: str = ""

    # ---- 46elks ----
    elks_api_username: str = ""
    elks_api_password: str = ""
    elks_default_sender_id: str = DEFAULT_SMS_SENDER_ID
    elks_webhook_secret: str = ""

    # ---- fortnox ----
    fortnox_client_id: str = ""
    fortnox_client_secret: str = ""
    fortnox_redirect_uri: str = "https://app.switchboard.se/api/integrations/fortnox/callback"

    # ---- visma eEkonomi ----
    visma_client_id: str = ""
    visma_client_secret: str = ""
    visma_redirect_uri: str = "https://app.switchboard.se/api/integrations/visma/callback"

    # ---- google oauth (used by both NextAuth and Calendar) ----
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_calendar_redirect_uri: str = "https://app.switchboard.se/api/integrations/google-calendar/callback"

    # ---- stripe billing ----
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""
    stripe_price_professional: str = ""
    stripe_price_premium: str = ""
    stripe_portal_return_url: str = "https://app.switchboard.se/settings"

    # ---- auth (NextAuth-issued JWT) ----
    auth_mode: AuthMode = AuthMode.DEV_HEADER
    auth_jwks_url: str = ""
    auth_audience: str = "switchboard-backend"
    auth_issuer: str = "https://app.switchboard.se"
    allowed_signup_domains: tuple[str, ...] = ()
    bootstrap_internal_token: str = ""

    # ---- observability ----
    sentry_dsn: str = ""
    sentry_environment: str | None = None

    # ---- cost telemetry rates (tune as GA pricing lands) ----
    # Vertex AI Live API token rates — estimates based on PRD §10.1.
    cost_rate_prompt_token_sek: float = 0.0000125
    cost_rate_response_token_sek: float = 0.000050
    # 46elks Sweden — inbound voice + SMS.
    cost_rate_telephony_minute_sek: float = 0.40
    cost_rate_sms_sek: float = 0.30
    cost_overhead_sek: float = 0.30

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def is_dev(self) -> bool:
        return self.env is Environment.DEV

    @property
    def is_prod(self) -> bool:
        return self.env is Environment.PROD


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
