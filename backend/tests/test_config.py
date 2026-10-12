"""Tests for configuration parsing and security constraints."""

import pytest
from pydantic import ValidationError
from app.core.config import Settings
from app.core.constants import AppEnvironment


def test_config_defaults():
    settings = Settings(
        APP_ENV=AppEnvironment.DEVELOPMENT,
        DATABASE_URL="sqlite:///./test.db",
        SUPABASE_JWT_SECRET="valid-long-secret-key-for-test-32chars!",
    )
    assert settings.APP_NAME == "NIDANA-Backend"
    assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_config_normalizes_postgres_url():
    settings = Settings(
        DATABASE_URL="postgres://user:pass@localhost:5432/dbname",
        SUPABASE_JWT_SECRET="valid-long-secret-key-for-test-32chars!",
    )
    assert settings.DATABASE_URL.startswith("postgresql+psycopg2://")


def test_production_disallows_cors_wildcard():
    with pytest.raises(ValidationError, match="CORS wildcard"):
        Settings(
            APP_ENV=AppEnvironment.PRODUCTION,
            CORS_ORIGINS=["*"],
            SUPABASE_JWT_SECRET="valid-production-secret-must-be-long-enough-32",
        )


def test_production_disallows_placeholder_secret():
    with pytest.raises(ValidationError, match="secure SUPABASE_JWT_SECRET"):
        Settings(
            APP_ENV=AppEnvironment.PRODUCTION,
            CORS_ORIGINS=["https://nidana.edu"],
            SUPABASE_JWT_SECRET="placeholder-secret",
        )
