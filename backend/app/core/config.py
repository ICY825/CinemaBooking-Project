from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Cinema Booking API"
    env: str = "dev"
    database_url: str = "sqlite:///./cinema.db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "dev-secret-change-me-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    reset_token_minutes: int = 30

    seat_hold_minutes: int = 10
    cors_origins: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]
    frontend_url: str = "http://localhost:8080"

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    mail_from: str = "no-reply@cinema.local"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
