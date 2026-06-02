from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PostureCoach"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/posturecoach", alias="DATABASE_URL")
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    auto_create_tables: bool = Field(default=True, alias="AUTO_CREATE_TABLES")

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
