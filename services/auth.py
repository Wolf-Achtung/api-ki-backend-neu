# -*- coding: utf-8 -*-
"""
Robuster Auth-Service mit Raw-SQL für Login-Codes.
Schema-tolerant und ohne ORM Clause-Element-Probleme.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Set, Tuple

from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import get_session

log_enabled = os.getenv("AUTH_DEBUG_LOG", "0") == "1"

# Konfiguration
DEFAULT_CODE_LENGTH = int(os.getenv("LOGIN_CODE_LENGTH", "6"))
DEFAULT_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
HASH_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))  # 30 Tage default


def _log(msg: str, *args) -> None:
    """Debug-Logging wenn aktiviert"""
    if log_enabled:
        import logging
        logging.getLogger("services.auth").debug(msg, *args)


def _utcnow() -> datetime:
    """Timezone-aware UTC now"""
    return datetime.now(timezone.utc)


def _hash_code(code: str, email: str) -> str:
    """Hasht den Code mit Email und Secret"""
    return hashlib.sha256(
        f"{code}:{email.lower()}:{HASH_SECRET}".encode("utf-8")
    ).hexdigest()


def _generate_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generiert einen numerischen Code"""
    # Sicherer als random
    max_val = 10 ** length
    code_int = secrets.randbelow(max_val)
    return str(code_int).zfill(length)


def _get_columns(db: Session, table: str) -> Set[str]:
    """Ermittelt vorhandene Spalten einer Tabelle"""
    try:
        result = db.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = :table
            """),
            {"table": table}
        )
        return {row[0] for row in result}
    except Exception:
        return set()


def _ensure_login_codes_table(db: Session) -> None:
    """Stellt sicher dass login_codes Tabelle existiert (idempotent)"""
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS login_codes (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                code VARCHAR(64) NOT NULL,
                purpose VARCHAR(40) DEFAULT 'login',
                created_at TIMESTAMPTZ DEFAULT now(),
                expires_at TIMESTAMPTZ NOT NULL,
                consumed_at TIMESTAMPTZ,
                attempts INTEGER DEFAULT 0,
                ip_address VARCHAR(64),
                user_agent TEXT
            );
        """))
        
        # Indizes
        for idx_sql in [
            "CREATE INDEX IF NOT EXISTS ix_login_codes_email ON login_codes(email)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_code ON login_codes(code)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes(consumed_at)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_created_at ON login_codes(created_at)",
        ]:
            db.execute(text(idx_sql))
        
        db.commit()
        _log("login_codes table ensured")
    except Exception as exc:
        _log("table setup warning (non-critical): %s", exc)
        db.rollback()


def generate_code(
    db: Session,
    user: Dict[str, any] | any,
    purpose: str = "login",
    ttl_minutes: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> str:
    """
    Generiert einen Login-Code und speichert ihn in login_codes.
    
    Args:
        db: SQLAlchemy Session
        user: Dict mit 'email' oder Objekt mit .email Attribut
        purpose: Zweck des Codes (default: 'login')
        ttl_minutes: TTL in Minuten (default: aus ENV)
        ip_address: Optional IP-Adresse
        user_agent: Optional User-Agent
        
    Returns:
        Der generierte Code (Klartext) - muss per Email versendet werden
        
    Raises:
        ValueError: Wenn user.email fehlt
        RuntimeError: Bei Datenbankfehlern
    """
    _ensure_login_codes_table(db)
    
    # Email extrahieren (dict oder Objekt)
    if isinstance(user, dict):
        email = user.get("email")
    else:
        email = getattr(user, "email", None)
    
    if not email:
        raise ValueError("User email is required")
    
    email = email.strip().lower()
    ttl = ttl_minutes or DEFAULT_TTL_MINUTES
    
    # Code generieren
    code = _generate_code()
    now = _utcnow()
    expires = now + timedelta(minutes=ttl)
    
    # Prüfe Schema
    cols = _get_columns(db, "login_codes")
    if not cols:
        raise RuntimeError("login_codes table not found")
    
    # Baue Insert dynamisch basierend auf vorhandenen Spalten
    values: Dict[str, any] = {
        "email": email,
        "code": code,  # Klartext für einfache Verifikation
        "created_at": now,
        "expires_at": expires,
    }
    
    if "purpose" in cols:
        values["purpose"] = purpose
    if "consumed_at" in cols:
        values["consumed_at"] = None
    if "attempts" in cols:
        values["attempts"] = 0
    if "ip_address" in cols and ip_address:
        values["ip_address"] = ip_address[:64]  # Limit length
    if "user_agent" in cols and user_agent:
        values["user_agent"] = user_agent[:500]  # Limit length
    
    # Insert
    cols_sql = ", ".join(values.keys())
    vals_sql = ", ".join(f":{k}" for k in values.keys())
    
    try:
        db.execute(
            text(f"INSERT INTO login_codes ({cols_sql}) VALUES ({vals_sql})"),
            values
        )
        db.commit()
        _log("Code generated for %s, expires at %s", email, expires)
        return code
        
    except Exception as exc:
        db.rollback()
        _log("generate_code failed: %s", exc)
        raise RuntimeError(f"Failed to generate code: {exc}")


def verify_code(
    db: Session,
    user: Dict[str, any] | any,
    code_input: str,
    purpose: str = "login",
    mark_consumed: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Verifiziert einen Login-Code.
    
    Args:
        db: SQLAlchemy Session
        user: Dict mit 'email' oder Objekt mit .email
        code_input: Vom User eingegebener Code
        purpose: Erwarteter Zweck (default: 'login')
        mark_consumed: Ob Code als verbraucht markiert werden soll
        
    Returns:
        Tuple (success: bool, error_reason: Optional[str])
        
    Error reasons:
        - "email_missing": User hat keine Email
        - "no_code": Kein passender Code gefunden
        - "expired": Code abgelaufen
        - "already_used": Code bereits verwendet
        - "max_attempts": Zu viele Versuche
    """
    _ensure_login_codes_table(db)
    
    # Email extrahieren
    if isinstance(user, dict):
        email = user.get("email")
    else:
        email = getattr(user, "email", None)
    
    if not email:
        return (False, "email_missing")
    
    email = email.strip().lower()
    code_input = code_input.strip()
    
    if not code_input:
        return (False, "no_code")
    
    # Schema prüfen
    cols = _get_columns(db, "login_codes")
    if not cols:
        return (False, "table_missing")
    
    # WHERE-Bedingungen bauen
    where_parts = [
        "LOWER(email) = LOWER(:email)",
        "code = :code",
    ]
    params = {"email": email, "code": code_input}
    
    if "purpose" in cols:
        where_parts.append("purpose = :purpose")
        params["purpose"] = purpose
    
    if "consumed_at" in cols:
        where_parts.append("consumed_at IS NULL")
    
    where_sql = " AND ".join(where_parts)
    order_by = "created_at DESC" if "created_at" in cols else "id DESC"
    
    try:
        # Hole den neuesten matching Code
        result = db.execute(
            text(f"""
                SELECT id, expires_at, consumed_at, attempts
                FROM login_codes
                WHERE {where_sql}
                ORDER BY {order_by}
                LIMIT 1
                FOR UPDATE  -- Lock für atomare Updates
            """),
            params
        ).mappings().first()
        
        if not result:
            _log("No matching code found for %s", email)
            return (False, "no_code")
        
        row_id = result["id"]
        expires_at = result["expires_at"]
        consumed_at = result.get("consumed_at")
        attempts = result.get("attempts", 0)
        
        # Prüfe ob abgelaufen
        if expires_at and _utcnow() > expires_at:
            _log("Code expired for %s", email)
            return (False, "expired")
        
        # Prüfe ob bereits verwendet
        if consumed_at is not None:
            _log("Code already used for %s", email)
            return (False, "already_used")
        
        # Prüfe Attempts (optional)
        max_attempts = int(os.getenv("LOGIN_CODE_MAX_ATTEMPTS", "5"))
        if "attempts" in cols and attempts >= max_attempts:
            _log("Max attempts reached for %s", email)
            return (False, "max_attempts")
        
        # ✅ Code ist gültig!
        
        if mark_consumed and "consumed_at" in cols:
            # Markiere als verbraucht
            db.execute(
                text("""
                    UPDATE login_codes 
                    SET consumed_at = now(),
                        attempts = attempts + 1
                    WHERE id = :id
                """),
                {"id": row_id}
            )
            db.commit()
            _log("Code consumed for %s", email)
        elif "attempts" in cols:
            # Inkrement attempts
            db.execute(
                text("UPDATE login_codes SET attempts = attempts + 1 WHERE id = :id"),
                {"id": row_id}
            )
            db.commit()
        
        return (True, None)
        
    except Exception as exc:
        db.rollback()
        _log("verify_code exception: %s", exc)
        return (False, "internal_error")


def cleanup_expired_codes(db: Session, older_than_hours: int = 24) -> int:
    """
    Löscht abgelaufene/alte Login-Codes (Maintenance).
    
    Returns:
        Anzahl gelöschter Codes
    """
    try:
        cutoff = _utcnow() - timedelta(hours=older_than_hours)
        result = db.execute(
            text("""
                DELETE FROM login_codes
                WHERE created_at < :cutoff
                  OR (consumed_at IS NOT NULL AND consumed_at < :cutoff)
                RETURNING id
            """),
            {"cutoff": cutoff}
        )
        count = len(result.fetchall())
        db.commit()
        _log("Cleaned up %d old codes", count)
        return count
    except Exception as exc:
        db.rollback()
        _log("cleanup failed: %s", exc)
        return 0


def get_code_stats(db: Session, email: str) -> Dict[str, int]:
    """
    Gibt Statistiken für einen User zurück (für Rate-Limiting).
    
    Returns:
        Dict mit: total, pending, consumed, expired
    """
    _ensure_login_codes_table(db)
    
    try:
        result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE consumed_at IS NULL AND expires_at > now()) as pending,
                    COUNT(*) FILTER (WHERE consumed_at IS NOT NULL) as consumed,
                    COUNT(*) FILTER (WHERE consumed_at IS NULL AND expires_at <= now()) as expired
                FROM login_codes
                WHERE LOWER(email) = LOWER(:email)
                  AND created_at > now() - interval '24 hours'
            """),
            {"email": email}
        ).mappings().first()
        
        return {
            "total": result["total"] or 0,
            "pending": result["pending"] or 0,
            "consumed": result["consumed"] or 0,
            "expired": result["expired"] or 0,
        }
    except Exception:
        return {"total": 0, "pending": 0, "consumed": 0, "expired": 0}


# ============================================================================
# JWT Token Funktionen
# ============================================================================

def create_access_token(email: str, user_id: Optional[int] = None) -> str:
    """
    Erstellt einen JWT Access Token.
    
    Args:
        email: User Email
        user_id: Optional User ID
        
    Returns:
        JWT Token String
    """
    expire = _utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    payload = {
        "sub": email,
        "email": email,
        "exp": expire,
        "iat": _utcnow(),
    }
    
    if user_id:
        payload["user_id"] = user_id
    
    token = jwt.encode(payload, HASH_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Optional[Dict[str, any]]:
    """
    Dekodiert und validiert einen JWT Token.
    
    Returns:
        Token Payload oder None bei Fehler
    """
    try:
        payload = jwt.decode(token, HASH_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        _log("Token decode failed: %s", exc)
        return None


# ============================================================================
# FastAPI Dependency: get_current_user
# ============================================================================

class UserDict(dict):
    """Simple User wrapper damit sowohl dict-access als auch attribute-access funktioniert"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
    
    def __setattr__(self, key, value):
        self[key] = value


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_session)
) -> UserDict:
    """
    FastAPI Dependency: Extrahiert und validiert User aus JWT Token.
    
    Args:
        authorization: Authorization Header (format: "Bearer <token>")
        db: Database Session
        
    Returns:
        User dict mit Attribut-Zugriff
        
    Raises:
        HTTPException: 401 wenn Token fehlt oder ungültig
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Token dekodieren
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("email") or payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=401,
            detail="Token missing email claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # User aus DB laden
    try:
        result = db.execute(
            text("SELECT * FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1"),
            {"email": email}
        ).mappings().first()
        
        if not result:
            # User existiert nicht - automatisch anlegen
            db.execute(
                text("""
                    INSERT INTO users (email, created_at, last_login_at)
                    VALUES (:email, now(), now())
                    ON CONFLICT DO NOTHING
                """),
                {"email": email}
            )
            db.commit()
            
            # Nochmal laden
            result = db.execute(
                text("SELECT * FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1"),
                {"email": email}
            ).mappings().first()
        else:
            # Update last_login_at
            db.execute(
                text("UPDATE users SET last_login_at = now() WHERE id = :id"),
                {"id": result["id"]}
            )
            db.commit()
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create/load user")
        
        # Konvertiere zu UserDict für kompatiblen Zugriff
        return UserDict(result)
        
    except HTTPException:
        raise
    except Exception as exc:
        _log("get_current_user failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
