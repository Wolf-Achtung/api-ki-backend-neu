
# settings.py
# -*- coding: utf-8 -*-
"""
Zentrale App-Settings für das KI‑Backend (Pydantic v2 kompatibel).

Fixes:
- Ersetzt `from pydantic import BaseSettings` durch `from pydantic_settings import BaseSettings`.
- Robuste Verarbeitung von ENV-Variablen (Bool/String/Liste).
- Automatischer Fallback zur Railway‑Postgres‑Konfiguration, wenn `DATABASE_URL` nicht direkt gesetzt ist.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _split_csv(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in str(value).split(",") if p.strip()]


def _railway_pg_url(env: dict) -> Optional[str]:
    """
    Bildet aus Railway-Variablen eine Postgres-URL, falls DATABASE_URL nicht direkt vorhanden ist.
    Beachtet folgende envs:
      - DATABASE_URL (bevorzugt)
      - POSTGRES_URL oder POSTGRESQL_URL
      - PGHOST, PGUSER, PGPASSWORD, PGDATABASE, PGPORT
    """
    if env.get("DATABASE_URL"):
        return env.get("DATABASE_URL")

    # Common Railway aliases
    for key in ("POSTGRES_URL", "POSTGRESQL_URL"):
        if env.get(key):
            return env[key]

    host = env.get("PGHOST") or env.get("POSTGRES_HOST")
    user = env.get("PGUSER") or env.get("POSTGRES_USER")
    pwd = env.get("PGPASSWORD") or env.get("POSTGRES_PASSWORD")
    db = env.get("PGDATABASE") or env.get("POSTGRES_DB") or env.get("POSTGRES_DATABASE")
    port = env.get("PGPORT") or env.get("POSTGRES_PORT", "5432")

    if all([host, user, pwd, db]):
        return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"

    return None


class Settings(BaseSettings):
    # Pydantic v2 Konfiguration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------------------
    # Allgemein
    # ---------------------
    APP_NAME: str = Field(default="KI Status Report API")
    ENV: Literal["production", "staging", "development", "test"] = Field(default="production")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # ---------------------
    # CORS
    # ---------------------
    CORS_ALLOW_ANY: bool = Field(default=False)
    CORS_ORIGINS: List[str] = Field(default_factory=list)

    # ---------------------
    # Auth / JWT
    # ---------------------
    JWT_SECRET: str = Field(default="changeme")  # in Railway via ENV überschreiben!
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_DAYS: int = Field(default=7)

    # ---------------------
    # Datenbank / Cache
    # ---------------------
    DATABASE_URL: Optional[str] = Field(default=None)
    REDIS_URL: Optional[str] = Field(default=None)

    # ---------------------
    # Email (Resend)
    # ---------------------
    RESEND_API_KEY: Optional[str] = Field(default=None)
    RESEND_FROM: Optional[str] = Field(default=None)

    # ---------------------
    # Normalisierungen
    # ---------------------
    @field_validator("CORS_ALLOW_ANY", mode="before")
    @classmethod
    def _norm_bool(cls, v) -> bool:
        return _as_bool(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _norm_origins(cls, v) -> List[str]:
        return _split_csv(v)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _fill_database_url(cls, v) -> Optional[str]:
        # Fallback auf Railway-ENV, falls None
        if v:
            return v
        import os
        return _railway_pg_url(os.environ)

    # ---------------------
    # Hilfsfunktionen
    # ---------------------
    def cors_allowed_origins(self) -> List[str]:
        if self.CORS_ALLOW_ANY:
            # Starlette erwartet dann kein origins-Array, Feature wird an anderer Stelle gesetzt
            return []
        return self.CORS_ORIGINS or []

    def is_production(self) -> bool:
        return self.ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Gecachter Settings-Zugriff (einmal pro Prozess auflösen)."""
    return Settings()


# Optional: sofortige Instanziierung für frühe Fehlererkennung beim Start
settings = get_settings()
