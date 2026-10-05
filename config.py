"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "FitBuddy"
    debug: bool = False

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_model: str = "gemini-2.5-flash-lite"
    gemini_timeout_seconds: int = 60
    gemini_temperature: float = 0.7

    # Server / security
    cors_origins: str = "*"
    rate_limit_per_minute: int = 20

    @property
    def has_api_key(self) -> bool:
        key = self.gemini_api_key.strip()
        return bool(key) and not key.lower().startswith("your_")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
