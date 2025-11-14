# -*- coding: utf-8 -*-
"""settings.py – Patch02 (Pydantic BaseSettings)
- Einheitliche Defaults für CORS & JWT
- Einfache Listenverarbeitung für CORS_ORIGINS (Komma-getrennt)
- LOG_LEVEL und APP_NAME als Basis
"""
from __future__ import annotations
import os
from typing import List
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    APP_NAME: str = Field(default="KI-Status API")
    LOG_LEVEL: str = Field(default="INFO")

    # JWT
    JWT_SECRET: str = Field(default="changeme")  # in Prod zwingend via ENV setzen!
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_DAYS: int = Field(default=7)
    JWT_ISS: str | None = Field(default=None)
    JWT_AUD: str | None = Field(default=None)

    # CORS
    CORS_ALLOW_ANY: int = Field(default=0)  # 1=alle Origins zulassen (nur Dev)
    CORS_ORIGINS: str = Field(default="https://make.ki-sicherheit.jetzt,https://www.make.ki-sicherheit.jetzt,https://ki-sicherheit.jetzt,https://www.ki-sicherheit.jetzt,https://ki-foerderung.jetzt")
    CORS_ALLOW_HEADERS: str = Field(default="authorization,content-type,idempotency-key")
    CORS_ALLOW_METHODS: str = Field(default="GET,POST,OPTIONS")

    def allowed_origins(self) -> List[str]:
        if self.CORS_ALLOW_ANY:
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        case_sensitive = False

settings = Settings()
