from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of cwd
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str

    APP_NAME: str = "Game Ops System"
    APP_VERSION: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        extra="ignore"
    )


settings = Settings()
