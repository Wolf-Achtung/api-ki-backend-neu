# -*- coding: utf-8 -*-
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import AnyHttpUrl

def _sanitize_origins(val: str | None, env: str) -> List[str]:
    if not val:
        return ["*"] if env != "production" else []
    raw = [x.strip() for x in val.split(",") if x.strip()]
    clean: list[str] = []
    for item in raw:
        # fix accidental double '://'
        if item.count("://") > 1:
            first, rest = item.split("://", 1)
            clean.append(first + "://" + rest.split("://")[0])
            last = rest.split("://")[-1]
            if last:
                clean.append("https://" + last)
        else:
            clean.append(item)
    # de-dup & drop empties
    return [x for i, x in enumerate(clean) if x and x not in clean[:i]]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)

    # App
    APP_NAME: str = "KI Status Report API"
    ENV: str = "development"
    VERSION: str = "2025.10"
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ALLOW_ORIGINS: str = ""
    @property
    def cors_origins(self) -> List[str]:
        return _sanitize_origins(self.CORS_ALLOW_ORIGINS, self.ENV)

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Auth
    JWT_SECRET: str = "change-me"
    TOKEN_EXP_MINUTES: int = 60 * 24
    CODE_EXP_MINUTES: int = 15
    ADMIN_EMAILS: str = ""   # new (comma-separated)
    ADMIN_EMAIL: str | None = None  # legacy fallback
    @property
    def admin_list(self) -> List[str]:
        parts = [*(self.ADMIN_EMAILS.split(",") if self.ADMIN_EMAILS else []), *( [self.ADMIN_EMAIL] if self.ADMIN_EMAIL else [])]
        return [p.strip().lower() for p in parts if p and p.strip()]

    # External services
    PDF_SERVICE_URL: Optional[AnyHttpUrl] = None
    PDF_TIMEOUT_MS: int = 90000  # ms (primary)
    PDF_TIMEOUT: int | None = None  # legacy alias in ms
    @property
    def pdf_timeout_ms(self) -> int:
        return int(self.PDF_TIMEOUT or self.PDF_TIMEOUT_MS or 90000)

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
    EXEC_SUMMARY_MODEL: Optional[str] = None
    OPENAI_TIMEOUT: float = 45.0
    OPENAI_MAX_TOKENS: int = 1500
    GPT_TEMPERATURE: float = 0.2

    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_TIMEOUT: float = 45.0
    OVERLAY_PROVIDER: str = "auto"

    # Optional live search
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None

settings = Settings()
