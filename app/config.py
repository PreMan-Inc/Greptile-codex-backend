from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables in production."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PreMan Demo API"
    app_env: Literal["development", "test", "demo", "production"] = "development"
    api_prefix: str = "/api/v1"
    storage_backend: Literal["memory", "dynamodb"] = "memory"
    table_name: str = "preman-demo-api"
    aws_region: str = "us-west-2"

    jwt_secret: str = Field(
        default="preman-hackathon-development-secret-change-me",
        min_length=32,
    )
    jwt_issuer: str = "preman-demo-api"
    access_token_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_days: int = Field(default=7, ge=1, le=90)
    reset_token_minutes: int = Field(default=15, ge=1, le=120)

    demo_user_email: str = "demo@preman.live"
    demo_user_password: str = Field(default="PremanDemo123!", min_length=8)
    expose_demo_tokens: bool = True
    cors_origins: str = "*"

    @property
    def allowed_origins(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
