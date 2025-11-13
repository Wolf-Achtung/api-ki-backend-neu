# core/security.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import logging, os
from typing import Any, Dict
import jwt  # PyJWT

try:
    from settings import settings  # type: ignore
except Exception:
    settings = None  # type: ignore

def _get(name: str, default: Any) -> Any:
    if settings is not None and hasattr(settings, name):
        val = getattr(settings, name)
        if val not in (None, ""):
            return val
    env_val = os.getenv(name)
    if env_val not in (None, ""):
        if name.endswith("_DAYS"):
            try:
                return int(env_val)
            except ValueError:
                logging.warning("Invalid int for %s=%r – using default %r", name, env_val, default)
                return default
        return env_val
    return default

JWT_SECRET: str = _get("JWT_SECRET", "")
if not JWT_SECRET:
    JWT_SECRET = os.urandom(32).hex()
    logging.warning("JWT_SECRET not set – using ephemeral secret. Tokens will invalidate on restart.")

JWT_ALGORITHM: str = _get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_DAYS: int = _get("JWT_EXPIRE_DAYS", 7)

def create_jwt(email: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=JWT_EXPIRE_DAYS)
    payload: Dict[str, Any] = {"sub": email, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

def bearer_from_header(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None
