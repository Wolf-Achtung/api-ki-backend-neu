
"""
core/security.py — JWT & Request-Helfer + Service-Token
"""
from __future__ import annotations
import hashlib
import hmac
import logging
import os
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


# ---------------------------------------------------------------------------
# Step 5 — JWT-Pflicht in Report-Pipeline-Endpoints (Wolf E5 Stufe 1)
#
# Umschaltbar via Env STEP5_JWT_ENFORCEMENT={1|true|yes}. Default: off
# (verhalten unverändert). Wenn aktiv:
#   - Endpoints lehnen unauthentisierte Requests mit 401 ab
#   - User-JWT muss in core.whitelist.EMAIL_WHITELIST stehen
#   - X-Service-Token mit Scope 'briefings:submit' bleibt zweiter Auth-Pfad
#
# Endpoints inspizieren ``principal.is_authenticated``/``.email``/``.is_service``
# um Owner-Checks und email-override-Strict-Equality zu fahren.
# ---------------------------------------------------------------------------


class AuthenticatedPrincipal(BaseModel):
    """Auth-Resultat für Step-5-Endpoints. Höchstens einer von email
    / service_principal ist gesetzt. ``is_authenticated`` ist False, wenn
    der Flag aus ist UND keine Auth-Header gefunden wurden — Endpoints
    fallen dann auf das Legacy-Verhalten zurück."""
    email: Optional[str] = None
    service_principal: Optional[str] = None
    is_service: bool = False
    is_authenticated: bool = False

    @property
    def identity(self) -> str:
        if self.is_service:
            return f"service:{self.service_principal}"
        if self.email:
            return f"user:{self.email}"
        return "anonymous"


def step5_jwt_enforcement_enabled() -> bool:
    """Read STEP5_JWT_ENFORCEMENT env on every request — Railway-flippable
    ohne Re-Deploy."""
    return (os.getenv("STEP5_JWT_ENFORCEMENT") or "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def step5_principal(
    auth_token: Optional[str] = Cookie(None, alias="auth_token"),
    authorization: Optional[str] = Header(None),
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
) -> AuthenticatedPrincipal:
    """Auth-Dependency für Schritt 5.

    Mit STEP5_JWT_ENFORCEMENT=on:
      - Service-Token vorhanden → muss valide sein, sonst 401/403
      - User-JWT vorhanden → muss valide UND whitelisted sein, sonst 401/403
      - Weder noch → 401

    Ohne Flag (Default):
      - Token wird best-effort ausgewertet, bei Fehler kommen wir mit
        is_authenticated=False zurück → Endpoints behalten das Legacy-
        Verhalten (kein Disruptions-Risiko).
    """
    enforced = step5_jwt_enforcement_enabled()
    s = get_settings()

    # Pfad 1: Service-Token
    if x_service_token and s.security.service_token_enabled:
        try:
            service_payload = verify_service_token(
                x_service_token, required_scope="briefings:submit"
            )
            return AuthenticatedPrincipal(
                service_principal=service_payload.principal,
                is_service=True,
                is_authenticated=True,
            )
        except HTTPException:
            if enforced:
                raise
            # Flag off: schlucken, weiter mit User-Pfad

    # Pfad 2: User-JWT (Cookie ODER Bearer)
    token = auth_token
    if not token and authorization:
        scheme, _, header_token = authorization.partition(" ")
        if scheme.lower() == "bearer" and header_token:
            token = header_token

    if token:
        try:
            user_payload = verify_access_token(token)
        except HTTPException:
            if enforced:
                raise
            return AuthenticatedPrincipal(is_authenticated=False)

        # Whitelist-Check (nur wenn enforced — sonst best-effort durchlassen)
        if enforced:
            try:
                from core.whitelist import is_whitelisted
            except ImportError:  # pragma: no cover
                is_whitelisted = lambda _e: True  # type: ignore[assignment]
            if not is_whitelisted(user_payload.email):
                log.warning(
                    "🚫 Step5: JWT for non-whitelisted email rejected: %s",
                    user_payload.email,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not whitelisted for the test phase.",
                )

        return AuthenticatedPrincipal(
            email=user_payload.email,
            is_authenticated=True,
        )

    # Pfad 3: keine Auth
    if enforced:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentication required (JWT cookie/bearer or X-Service-Token)."
            ),
        )
    return AuthenticatedPrincipal(is_authenticated=False)


def resolve_pipeline_email(
    principal: AuthenticatedPrincipal,
    body_email: Optional[str],
) -> Optional[str]:
    """
    Welche E-Mail soll die Pipeline als Empfänger nutzen?

    Regeln:
      - Service-Token (Golden Reports, CI): body_email zählt — Service darf
        die Empfänger-Email frei setzen.
      - User-JWT: body_email muss case-insensitive == principal.email sein,
        wenn gesetzt; sonst 403. Returns principal.email (single source of
        truth, body wird ignoriert).
      - Unauthenticated (Flag aus): body_email durchreichen (Legacy).

    Raises HTTPException 403 bei mismatch.
    """
    if principal.is_service:
        return body_email
    if principal.is_authenticated and principal.email:
        if body_email and body_email.strip().lower() != principal.email.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="email/email_override must match the token email.",
            )
        return principal.email
    # Legacy passthrough
    return body_email
