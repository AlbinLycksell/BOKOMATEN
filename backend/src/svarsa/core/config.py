from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", REPO_ROOT / ".env.local"),
        env_file_encoding="utf-8",
        env_prefix="SVARSA_",
        extra="ignore",
        case_sensitive=False,
    )

    env: Literal["dev", "staging", "prod"] = "dev"
    version: str = "0.1.0"

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")

    database_url: str = f"sqlite:///{REPO_ROOT / 'backend' / 'svarsa.db'}"
    seed_dev_data: bool = True

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = "models/gemini-3.1-flash-live-preview"
    gemini_voice: str = "Aoede"
    gemini_language: str = "sv-SE"

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False

    # Realtime Bridge → Application Backend boundary (PRD §8.2 / §8.10).
    # In dev (single deployable), the bridge dispatches tools in-process.
    # In prod (separate Cloud Run services), it calls Application Backend
    # over HTTPS so the two can deploy independently.
    tool_dispatch_mode: Literal["local", "http"] = "local"
    application_backend_url: str = "http://127.0.0.1:8000"
    bridge_internal_token: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
