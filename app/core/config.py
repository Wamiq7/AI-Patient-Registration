from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def to_sqlalchemy_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url.removeprefix("postgres://")
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url.removeprefix("postgresql://")
    if "neon.tech" in url and "sslmode=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Patient Registration API"
    app_env: str = "development"
    debug: bool = True
    database_url: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    vapi_api_key: str = ""

    @property
    def sqlalchemy_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not set")
        return to_sqlalchemy_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
