# -*- coding: utf-8 -*-
"""Central settings (Pydantic v2) for KI-Status-Report backend."""
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

    # External services
    PDF_SERVICE_URL: Optional[AnyHttpUrl] = None
    PDF_TIMEOUT_MS: int = 90000

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

    # Live / search
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None
    SEARCH_DAYS_NEWS: int = 30
    SEARCH_DAYS_TOOLS: int = 60
    SEARCH_DAYS_FUNDING: int = 60
    LIVE_MAX_ITEMS: int = 8

    # Data & prompts
    APP_BASE: str = "."
    DATA_DIR: str = "data"
    PROMPTS_DIR: str = "prompts"
    TEMPLATE_DIR: str = "templates"
    CONTENT_DIR: str = "content"
    TEMPLATE_DE: str = "pdf_template.html"
    TEMPLATE_EN: str = "pdf_template_en.html"
    ASSETS_BASE_URL: str = "/assets"

    # Auth / Security
    JWT_SECRET: str = "change-me"  # to be set via env in production

settings = Settings()
