# -*- coding: utf-8 -*-
"""
core/security.py
------------------------------------------------------------------
Minimal, robuste JWT-Helfer auf Basis von PyJWT.
- Liest Konfiguration aus ENV:
    JWT_SECRET        (erforderlich; sinnvoller Default für Dev)
    JWT_ALGORITHM     (Default: HS256)
    JWT_EXPIRE_DAYS   (Default: 7)
    JWT_ISSUER        (optional; Default: "ki-status-api")
- Bietet:
    create_jwt(email: str) -> str
    decode_jwt(token: str) -> dict | None
------------------------------------------------------------------
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

try:
    import jwt  # PyJWT
except Exception as e:  # pragma: no cover
    raise RuntimeError("PyJWT ist nicht installiert. Bitte 'PyJWT>=2.8.0' in requirements.txt aufnehmen.") from e


class Settings:
    def __init__(self) -> None:
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        # **WICHTIG**: Standardwert setzen, damit Attribut garantiert existiert
        try:
            self.JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
        except Exception:
            self.JWT_EXPIRE_DAYS = 7
        self.JWT_ISSUER: str = os.getenv("JWT_ISSUER", "ki-status-api")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Settings(alg={self.JWT_ALGORITHM}, days={self.JWT_EXPIRE_DAYS})"


settings = Settings()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_jwt(email: str) -> str:
    """
    Erzeugt ein signiertes JWT für die angegebene E-Mail.
    Claims: iss, sub, email, iat, exp
    """
    now = _now()
    exp = now + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "iss": settings.JWT_ISSUER,
        "sub": email,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    # PyJWT 2.x gibt unter Py3 immer str zurück
    return token  # type: ignore[return-value]


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Dekodiert/verifiziert ein JWT. Liefert Payload oder None.
    """
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return dict(data)
    except Exception:
        return None
