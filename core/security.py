
"""
core/security.py — JWT & Request-Helfer + Service-Token
"""
from __future__ import annotations
import hashlib
import hmac
import logging
import time
from typing import Optional, Tuple, Union

import jwt
from fastapi import Cookie, Header, HTTPException, status
from pydantic import BaseModel

from settings import get_settings

log = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    sub: str
    email: str
    iat: int
    exp: int


class ServiceTokenPayload(BaseModel):
    """Payload für Service-Token (headless/automated access)."""
    sub: str = "service"
    principal: str  # z.B. "golden_reports", "ci_runner"
    scope: str = "briefings:submit"  # erlaubte Scopes


def create_access_token(email: str, subject: str = "user") -> str:
    s = get_settings()
    now = int(time.time())
    exp = now + s.security.jwt_expire_days * 24 * 60 * 60
    payload = {"sub": subject, "email": email, "iat": now, "exp": exp}
    token = jwt.encode(payload, s.security.jwt_secret, algorithm=s.security.jwt_algorithm)
    return str(token)


def verify_access_token(token: str) -> TokenPayload:
    s = get_settings()
    try:
        data = jwt.decode(token, s.security.jwt_secret, algorithms=[s.security.jwt_algorithm])
        return TokenPayload(**data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def bearer_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return token


def get_current_user(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> TokenPayload:
    """
    Phase 1 Hybrid Mode: Accept tokens from httpOnly cookies (priority) or Authorization headers.

    This dependency checks for authentication in the following order:
    1. httpOnly cookie (auth_token) - preferred method
    2. Authorization header (Bearer token) - fallback for backward compatibility

    Returns:
        TokenPayload: The verified token payload containing user information

    Raises:
        HTTPException: 401 if no valid token is found
    """
    token = None

    # Priority 1: Check httpOnly cookie
    if auth_token:
        token = auth_token
    # Fallback: Check Authorization header
    elif authorization:
        scheme, _, header_token = authorization.partition(" ")
        if scheme.lower() == "bearer" and header_token:
            token = header_token

    # No token found in either location
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide token via cookie or Authorization header."
        )

    # Verify and return token payload
    return verify_access_token(token)


# ---------------------------------------------------------------------------
# Service-Token für headless/automated API-Zugriff
# ---------------------------------------------------------------------------

def verify_service_token(token: str, required_scope: str = "briefings:submit") -> ServiceTokenPayload:
    """
    Verifiziert einen Service-Token für headless API-Zugriff.

    Format: <principal>:<secret>
    Beispiel: golden_reports:abc123...

    Args:
        token: Service-Token im Format principal:secret
        required_scope: Benötigter Scope (default: briefings:submit)

    Returns:
        ServiceTokenPayload bei Erfolg

    Raises:
        HTTPException 401: Token ungültig oder disabled
        HTTPException 403: Scope nicht erlaubt
    """
    s = get_settings()

    # Feature-Flag prüfen
    if not s.security.service_token_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service-Token authentication is disabled"
        )

    # Secret muss konfiguriert sein
    if not s.security.service_token_secret:
        log.error("SERVICE_TOKEN_SECRET not configured but SERVICE_TOKEN_ENABLED=1")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service authentication misconfigured"
        )

    # Token-Format prüfen: principal:secret
    if ":" not in token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token format"
        )

    principal, provided_secret = token.split(":", 1)

    # Erlaubte Principals (erweiterbar)
    allowed_principals = {"golden_reports", "ci_runner", "test_runner"}
    if principal not in allowed_principals:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown service principal"
        )

    # Secret prüfen (timing-safe comparison)
    expected_secret = s.security.service_token_secret
    if not hmac.compare_digest(provided_secret, expected_secret):
        log.warning("Invalid service token for principal: %s", principal)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token"
        )

    # Scope-Mapping pro Principal
    principal_scopes = {
        "golden_reports": ["briefings:submit", "reports:read"],
        "ci_runner": ["briefings:submit"],
        "test_runner": ["briefings:submit", "reports:read"],
    }

    allowed_scopes = principal_scopes.get(principal, [])
    if required_scope not in allowed_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Scope '{required_scope}' not allowed for principal '{principal}'"
        )

    log.info("Service-Token authenticated: principal=%s scope=%s", principal, required_scope)
    return ServiceTokenPayload(principal=principal, scope=required_scope)


def get_service_or_user_auth(
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
) -> Union[ServiceTokenPayload, TokenPayload]:
    """
    Kombinierte Auth-Dependency: Service-Token ODER User-Auth.

    Priorität:
    1. X-Service-Token Header (wenn SERVICE_TOKEN_ENABLED=1)
    2. Cookie auth_token
    3. Authorization Bearer Header

    Returns:
        ServiceTokenPayload oder TokenPayload

    Raises:
        HTTPException 401: Keine gültige Authentifizierung
    """
    s = get_settings()

    # 1. Service-Token (wenn enabled und vorhanden)
    if x_service_token and s.security.service_token_enabled:
        return verify_service_token(x_service_token)

    # 2. Fallback: normale User-Auth
    return get_current_user(auth_token, authorization)
