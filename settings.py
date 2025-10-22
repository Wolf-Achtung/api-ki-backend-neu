# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # Meta
    APP_NAME: str = "KI-Status-Report API"
    VERSION: str = "1.0.0"
    ENV: str = "production"      # production | staging | development
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str

    # Auth / JWT
    JWT_SECRET: str = "change-me"   # override in production
    TOKEN_MINUTES: int = 60*24      # legacy alias (kept for safety)
    TOKEN_EXP_MINUTES: int = 60*24  # preferred
    CODE_EXP_MINUTES: int = 15

    # Admins
    ADMIN_EMAILS: str = ""          # comma-separated
    ADMIN_EMAIL: Optional[str] = None

    # CORS
    CORS_ORIGINS: str = ""          # comma separated
    CORS_ALLOW_ANY: bool = False    # if true or if CORS_ORIGINS empty & ENV!=production, allow any http(s)

    # LLM
    OPENING_REM: str = ""           # reserved
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_API_BASE: Optional[str] = None

    # PDF
    PDF_SERVICE_URL: Optional[str] = None

    # SMTP (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_FROM_NAME: str = "KI-Readiness"
    SMTP_TLS: bool = True

    # ---- Helpers ----
    def cors_list(self) -> List[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return []
        items = [s.strip().rstrip("/") for s in raw.split(",") if s.strip()]
        seen = set()
        out: List[str] = []
        for x in items:
            if x not in seen:
                seen.add(x); out.append(x)
        return out

    @property
    def allow_any_cors(self) -> bool:
        return bool(self.CORS_ALLOW_ANY) or (not self.cors_list() and self.maybe_non_prod())

    def maybe_non_prod(self) -> bool:
        return (self.ENV or "").lower() != "production"

    def admin_list(self) -> List[str]:
        vals = []
        if self.ADMIN_EMAILS:
            vals.extend([p.strip().lower() for p in self.ADMIN_EMAILS.split(",") if p and p.strip()])
        if self.ADMIN_EMAIL:
            vals.append(self.ADMIN_EMAIL.strip().lower())
        # dedupe
        seen = set(); out = []
        for v in vals:
            if v and v not in seen:
                seen.add(v); out.append(v)
        return out

settings = Settings()
