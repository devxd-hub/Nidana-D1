"""Application settings and configuration management using pydantic-settings."""

import os
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import AppEnvironment


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General App Config
    APP_NAME: str = "NIDANA-Backend"
    APP_VERSION: str = "0.1.0"
    APP_ENV: AppEnvironment = AppEnvironment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database connection
    # Defaults to local sqlite for hermetic dev/testing if not specified.
    DATABASE_URL: str = Field(
        default="sqlite:///./nidana_dev.db",
        description="SQLAlchemy database URL for PostgreSQL/Supabase or SQLite.",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        # Standardize postgres:// to postgresql+psycopg2:// for SQLAlchemy
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://") and "+psycopg2" not in v:
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    # Supabase Authentication & Project Settings
    SUPABASE_URL: str = Field(
        default="https://placeholder.supabase.co",
        description="Supabase project URL",
    )
    SUPABASE_ANON_KEY: str = Field(
        default="placeholder-anon-key",
        description="Supabase anonymous client key",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="",
        description="Supabase service role secret (server-side only, never leak)",
    )
    SUPABASE_JWT_SECRET: str = Field(
        default="nidana-dev-secret-key-32-chars-minimum-sample!!",
        description="Supabase JWT secret for server-side token signature verification",
    )
    SUPABASE_JWT_AUDIENCE: str = Field(
        default="authenticated",
        description="Expected audience in Supabase JWTs",
    )
    SUPABASE_JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Expected JWT signature algorithm",
    )

    # Security Guardrails Validation
    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.APP_ENV == AppEnvironment.PRODUCTION:
            if "*" in self.CORS_ORIGINS:
                raise ValueError("CORS wildcard ('*') is strictly disallowed in production environment.")
            if "placeholder" in self.SUPABASE_JWT_SECRET or len(self.SUPABASE_JWT_SECRET) < 16:
                raise ValueError("A secure SUPABASE_JWT_SECRET must be configured in production.")
        return self


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
