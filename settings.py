# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Meta
    APP_NAME: str = Field(default="KI-Status-Report API")
    VERSION: str = Field(default="1.0.0")
    ENV: str = Field(default="production")
    LOG_LEVEL: str = Field(default="INFO")

    # DB
    DATABASE_URL: str

    # CORS
    CORS_ORIGINS: str = Field(default="")  # comma-separated list
    CORS_ALLOW_ANY: bool = Field(default=False)  # if true, use allow_origin_regex
    def cors_list(self) -> List[str]:
        s = (self.CORS_ORIGINS or "").strip()
        if not s:
            return []
        items = [x.strip().rstrip("/") for x in s.split(",") if x.strip()]
        return items

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")

    # PDF
    PDF_SERVICE_URL: Optional[str] = None

settings = Settings()
