# -*- coding: utf-8 -*-
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)

    # App
    APP_NAME: str = "KI Status Report API"
    ENV: str = "development"
    VERSION: str = "2025.10"
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ALLOW_ORIGINS: str = ""  # comma-separated list
    @property
    def cors_origins(self) -> List[str]:
        if not self.CORS_ALLOW_ORIGINS:
            return ["*"] if self.ENV != "production" else []
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Auth
    JWT_SECRET: str = "change-me"
    TOKEN_EXP_MINUTES: int = 60 * 24
    CODE_EXP_MINUTES: int = 15
    ADMIN_EMAILS: str = ""  # comma-separated list

    # External services
    PDF_SERVICE_URL: Optional[AnyHttpUrl] = None
    PDF_TIMEOUT_MS: int = 90000

    # Mail (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_FROM_NAME: str = "KI-Readiness"
    SMTP_TLS: bool = True

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_DEFAULT: str = "gpt-4o"
    OPENAI_TIMEOUT: float = 45.0
    OPENAI_MAX_TOKENS: int = 1500
    GPT_TEMPERATURE: float = 0.2

    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_TIMEOUT: float = 45.0
    OVERLAY_PROVIDER: str = "auto"

    # Live / search (optional)
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None

settings = Settings()
