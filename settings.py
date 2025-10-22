# -*- coding: utf-8 -*-
"""Settings (Pydantic v2) – fixed import for Railway crash."""
from __future__ import annotations
from typing import List, Optional
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Meta
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    APP_NAME: str = Field("KI-Status-Report API", alias="APP_NAME")
    VERSION: str = Field("1.0.0", alias="VERSION")
    ENV: str = Field("production", alias="ENV")
    LOG_LEVEL: str = Field("INFO", alias="LOG_LEVEL")

    # DB
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")

    # CORS
    CORS_ORIGINS: str = Field("", alias="CORS_ORIGINS")
    @property
    def cors_origins(self) -> List[str]:
        s = (self.CORS_ORIGINS or "").strip()
        if not s:
            return []
        return [x.strip() for x in s.split(",") if x.strip()]

    # LLM
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    OPENAI_API_BASE: Optional[str] = Field(default=None, alias="OPENAI_API_BASE")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # PDF
    PDF_SERVICE_URL: Optional[AnyHttpUrl] = Field(default=None, alias="PDF_SERVICE_URL")

settings = Settings()
