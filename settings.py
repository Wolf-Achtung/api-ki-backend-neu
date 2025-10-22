# -*- coding: utf-8 -*-
from __future__ import annotations
from pydantic import BaseSettings, Field, AnyHttpUrl
from typing import List, Optional

class Settings(BaseSettings):
    APP_NAME: str = "KI-Status-Report API"
    VERSION: str = "1.0.0"
    ENV: str = Field("production", env="ENV")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # CORS
    CORS_ORIGINS: str = Field("", env="CORS_ORIGINS")
    @property
    def cors_origins(self) -> List[str]:
        s = (self.CORS_ORIGINS or "").strip()
        if not s:
            return []
        return [x.strip() for x in s.split(",") if x.strip()]

    # LLM Provider
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: Optional[str] = Field(None, env="OPENAI_API_BASE")
    OPENAI_MODEL: str = Field("gpt-4o-mini", env="OPENAI_MODEL")

    # PDF Service
    PDF_SERVICE_URL: Optional[AnyHttpUrl] = Field(None, env="PDF_SERVICE_URL")

    # E-Mail (optional)
    SMTP_HOST: Optional[str] = Field(None, env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASS: Optional[str] = Field(None, env="SMTP_PASS")
    EMAIL_FROM: Optional[str] = Field(None, env="EMAIL_FROM")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
