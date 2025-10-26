# -*- coding: utf-8 -*-
"""
Auth Router - Login via Magic Code (Email-basiert).
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.db import get_session
from services.auth import (
    generate_code,
    verify_code,
    create_access_token,
    get_current_user,
    get_code_stats,
)

log = logging.getLogger("routes.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RequestCodePayload(BaseModel):
    """Payload für Code-Anforderung"""
    email: EmailStr


class LoginPayload(BaseModel):
    """Payload für Login"""
    email: EmailStr
    code: str


class TokenResponse(BaseModel):
    """Token Response"""
    access_token: str
    token_type: str = "bearer"
    user: Dict


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/request-code")
def request_login_code(
    payload: RequestCodePayload,
    request: Request,
    db: Session = Depends(get_session)
):
    """
    Fordert einen Login-Code für eine Email-Adresse an.
    
    Der Code wird per Email versendet (muss extern implementiert werden).
    """
    email = payload.email.lower().strip()
    
    # Rate-Limiting Check
    stats = get_code_stats(db, email)
    
    # Maximal 5 pending codes pro 24h
    if stats["pending"] >= 5:
        raise HTTPException(
            status_code=429,
            detail="Too many pending codes. Please wait or use existing code."
        )
    
    # Maximal 10 codes total pro 24h
    if stats["total"] >= 10:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # IP-Adresse extrahieren
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    try:
        # Code generieren
        code = generate_code(
            db=db,
            user={"email": email},
            purpose="login",
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # TODO: Hier Email senden mit dem Code
        # send_login_code_email(email, code)
        
        log.info("Login code generated for %s", email)
        
        return {
            "ok": True,
            "message": "Login code sent to your email",
            "email": email,
            # DEV ONLY: Code in Response (in Production entfernen!)
            "code": code if log.level <= logging.DEBUG else None
        }
        
    except Exception as exc:
        log.error("Failed to generate code for %s: %s", email, exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate login code"
        )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginPayload,
    db: Session = Depends(get_session)
):
    """
    Validiert einen Login-Code und gibt einen JWT Access Token zurück.
    """
    email = payload.email.lower().strip()
    code = payload.code.strip()
    
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
    
    # Code verifizieren
    success, error_reason = verify_code(
        db=db,
        user={"email": email},
        code_input=code,
        purpose="login",
        mark_consumed=True
    )
    
    if not success:
        error_messages = {
            "no_code": "Invalid or expired code",
            "expired": "Code has expired",
            "already_used": "Code has already been used",
            "max_attempts": "Too many failed attempts",
            "email_missing": "Email is required",
            "internal_error": "Internal server error"
        }
        
        message = error_messages.get(error_reason, "Invalid code")
        status_code = 401 if error_reason in ["no_code", "expired", "already_used"] else 500
        
        raise HTTPException(status_code=status_code, detail=message)
    
    # ✅ Code gültig - User laden oder erstellen
    from sqlalchemy import text
    
    result = db.execute(
        text("SELECT * FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1"),
        {"email": email}
    ).mappings().first()
    
    if not result:
        # User anlegen
        db.execute(
            text("""
                INSERT INTO users (email, created_at, last_login_at)
                VALUES (:email, now(), now())
            """),
            {"email": email}
        )
        db.commit()
        
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
    
    # JWT Token erstellen
    access_token = create_access_token(
        email=email,
        user_id=result["id"]
    )
    
    log.info("User %s logged in successfully", email)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": result["id"],
            "email": result["email"],
            "is_admin": result.get("is_admin", False),
            "created_at": str(result.get("created_at")),
            "last_login_at": str(result.get("last_login_at"))
        }
    )


@router.get("/me")
def get_current_user_info(
    user = Depends(get_current_user)
):
    """
    Gibt Informationen über den aktuell eingeloggten User zurück.
    
    Requires: Authorization Header mit Bearer Token
    """
    return {
        "ok": True,
        "user": {
            "id": user.get("id"),
            "email": user.get("email"),
            "is_admin": user.get("is_admin", False),
            "created_at": str(user.get("created_at")),
            "last_login_at": str(user.get("last_login_at"))
        }
    }


@router.post("/logout")
def logout(
    user = Depends(get_current_user)
):
    """
    Logout-Endpoint (hauptsächlich Client-seitig).
    
    JWT Tokens können nicht serverseitig invalidiert werden,
    aber Client sollte Token löschen.
    """
    log.info("User %s logged out", user.get("email"))
    
    return {
        "ok": True,
        "message": "Logged out successfully"
    }


@router.get("/stats")
def auth_stats(
    email: str,
    db: Session = Depends(get_session)
):
    """
    Gibt Code-Statistiken für eine Email zurück (für Debug/Admin).
    """
    stats = get_code_stats(db, email)
    
    return {
        "ok": True,
        "email": email,
        "stats": stats
    }
