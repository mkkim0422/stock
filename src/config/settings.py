"""환경 설정 로더 (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    mode: str = "paper"
    log_level: str = "INFO"
    db_path: Path = Path("data/db/swing.db")

    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    turso_database_url: str | None = None
    turso_auth_token: str | None = None

    fx_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
