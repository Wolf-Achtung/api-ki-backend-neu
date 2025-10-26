# -*- coding: utf-8 -*-
"""
Konsolidierter Briefings-Router mit Draft-Management und Async-Submit.
Vereint alle Briefing-Endpunkte in einem Router.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import get_session
from models import Briefing, User

log = logging.getLogger("routes.briefings")
router = APIRouter(prefix="/briefings", tags=["briefings"])

# ============================================================================
# Hilfsfunktionen
# ============================================================================

def _get_current_user_safe(request: Request) -> Optional[Dict[str, Any]]:
    """Versucht den aktuellen User zu ermitteln - gibt None zurück bei Fehler"""
    try:
        from services.auth import get_current_user
        # Simuliere Depends-Verhalten
        user = get_current_user(request.headers.get("authorization"))
        return {"id": getattr(user, "id", None), "email": getattr(user, "email", None)}
    except Exception:
        return None


def _ensure_drafts_table(db: Session) -> None:
    """Erstellt briefing_drafts Tabelle falls nicht vorhanden (idempotent)"""
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS briefing_drafts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                email TEXT NOT NULL,
                lang VARCHAR(5) NOT NULL DEFAULT 'de',
                payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            );
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_briefing_drafts_email 
            ON briefing_drafts(email);
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_briefing_drafts_user_id 
            ON briefing_drafts(user_id);
        """))
        db.commit()
    except Exception as exc:
        log.warning("briefing_drafts table setup warning: %s", exc)
        db.rollback()


def _infer_email(payload: Dict[str, Any], user: Optional[Dict]) -> Optional[str]:
    """Ermittelt E-Mail aus verschiedenen Quellen"""
    # Direkt aus payload
    for key in ["email", "e_mail", "kontakt_email", "kontaktEmail"]:
        val = payload.get(key)
        if val and isinstance(val, str) and "@" in val:
            return val.strip().lower()
    
    # Aus nested answers
    answers = payload.get("answers", {})
    if isinstance(answers, dict):
        for key in ["email", "kontakt_email"]:
            val = answers.get(key)
            if val and isinstance(val, str) and "@" in val:
                return val.strip().lower()
    
    # Aus User
    if user and user.get("email"):
        return user["email"].strip().lower()
    
    return None


def _start_async_analysis(bg: BackgroundTasks, briefing_id: int, email: Optional[str]) -> bool:
    """Startet asynchrone Analyse wenn gpt_analyze verfügbar ist"""
    try:
        from gpt_analyze import run_async
        bg.add_task(run_async, briefing_id, email)
        log.info("Async analysis queued for briefing_id=%s", briefing_id)
        return True
    except ImportError:
        log.warning("gpt_analyze.run_async not available - analysis not queued")
        return False
    except Exception as exc:
        log.exception("Failed to queue async analysis: %s", exc)
        return False


# ============================================================================
# Pydantic Models
# ============================================================================

class DraftPayload(BaseModel):
    """Draft speichern"""
    lang: str = Field(default="de", max_length=5)
    answers: Dict[str, Any] = Field(default_factory=dict)
    email: Optional[str] = None


class BriefingSubmit(BaseModel):
    """Finales Briefing einreichen"""
    lang: str = Field(default="de", max_length=5)
    answers: Dict[str, Any]
    email: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/draft")
def get_draft(
    request: Request,
    db: Session = Depends(get_session),
):
    """
    Lädt den aktuellen Draft für den User/Email.
    
    Query-Parameter:
    - email: Optional - überschreibt User-Email
    """
    _ensure_drafts_table(db)
    
    user = _get_current_user_safe(request)
    email = request.query_params.get("email") or (user.get("email") if user else None)
    
    if not email:
        return {"ok": True, "draft": None, "reason": "no_email"}
    
    try:
        row = db.execute(
            text("""
                SELECT id, email, lang, payload, updated_at 
                FROM briefing_drafts 
                WHERE LOWER(email) = LOWER(:email)
                ORDER BY updated_at DESC 
                LIMIT 1
            """),
            {"email": email}
        ).mappings().first()
        
        if not row:
            return {"ok": True, "draft": None}
        
        return {
            "ok": True,
            "draft": {
                "id": row["id"],
                "email": row["email"],
                "lang": row["lang"],
                "answers": row["payload"],
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
        }
    except Exception as exc:
        log.exception("get_draft failed: %s", exc)
        raise HTTPException(status_code=500, detail="draft_load_failed")


@router.put("/draft")
def put_draft(
    payload: DraftPayload,
    request: Request,
    db: Session = Depends(get_session),
):
    """
    Speichert/aktualisiert einen Draft.
    
    Benötigt entweder:
    - payload.email ODER
    - authentifizierten User
    """
    _ensure_drafts_table(db)
    
    user = _get_current_user_safe(request)
    email = _infer_email({"email": payload.email, "answers": payload.answers}, user)
    
    if not email:
        # Kein Fehler - Frontend kann noch keine Email haben (Schritt 1)
        return {"ok": False, "skipped": True, "reason": "email_missing"}
    
    try:
        # Upsert-Logik
        db.execute(
            text("""
                INSERT INTO briefing_drafts (email, user_id, lang, payload, created_at, updated_at)
                VALUES (:email, :user_id, :lang, :payload::jsonb, now(), now())
                ON CONFLICT (email) 
                DO UPDATE SET 
                    lang = EXCLUDED.lang,
                    payload = EXCLUDED.payload,
                    updated_at = now()
            """),
            {
                "email": email,
                "user_id": user.get("id") if user else None,
                "lang": payload.lang,
                "payload": json.dumps(payload.answers),
            }
        )
        
        # Unique constraint könnte fehlen - Alternative Update/Insert
        if db.execute(text("SELECT 1")).scalar() is None:
            # Fallback für Datenbanken ohne ON CONFLICT
            existing = db.execute(
                text("SELECT id FROM briefing_drafts WHERE LOWER(email) = LOWER(:email)"),
                {"email": email}
            ).scalar()
            
            if existing:
                db.execute(
                    text("""
                        UPDATE briefing_drafts 
                        SET lang=:lang, payload=:payload::jsonb, updated_at=now()
                        WHERE LOWER(email)=LOWER(:email)
                    """),
                    {"email": email, "lang": payload.lang, "payload": json.dumps(payload.answers)}
                )
            else:
                db.execute(
                    text("""
                        INSERT INTO briefing_drafts (email, user_id, lang, payload, created_at, updated_at)
                        VALUES (:email, :user_id, :lang, :payload::jsonb, now(), now())
                    """),
                    {
                        "email": email,
                        "user_id": user.get("id") if user else None,
                        "lang": payload.lang,
                        "payload": json.dumps(payload.answers),
                    }
                )
        
        db.commit()
        return {"ok": True, "email": email}
        
    except Exception as exc:
        log.exception("put_draft failed: %s", exc)
        db.rollback()
        raise HTTPException(status_code=500, detail="draft_save_failed")


@router.delete("/draft")
def delete_draft(
    request: Request,
    db: Session = Depends(get_session),
):
    """Löscht den Draft für den aktuellen User"""
    _ensure_drafts_table(db)
    
    user = _get_current_user_safe(request)
    if not user or not user.get("email"):
        raise HTTPException(status_code=401, detail="authentication_required")
    
    try:
        result = db.execute(
            text("DELETE FROM briefing_drafts WHERE LOWER(email) = LOWER(:email) RETURNING id"),
            {"email": user["email"]}
        )
        deleted = result.scalar() is not None
        db.commit()
        return {"ok": True, "deleted": deleted}
        
    except Exception as exc:
        log.exception("delete_draft failed: %s", exc)
        db.rollback()
        raise HTTPException(status_code=500, detail="draft_delete_failed")


@router.get("/me/latest")
def get_my_latest(
    request: Request,
    db: Session = Depends(get_session),
):
    """
    Gibt das neueste finalisierte Briefing oder Draft zurück.
    
    Query-Parameter:
    - email: Optional - überschreibt User-Email
    """
    user = _get_current_user_safe(request)
    email = request.query_params.get("email") or (user.get("email") if user else None)
    
    if not email:
        return {"ok": True, "briefing": None, "reason": "no_email"}
    
    try:
        # 1. Versuche finalisiertes Briefing zu finden
        briefing_row = db.execute(
            text("""
                SELECT b.id, b.lang, b.answers, b.created_at
                FROM briefings b
                LEFT JOIN users u ON b.user_id = u.id
                WHERE LOWER(u.email) = LOWER(:email)
                ORDER BY b.created_at DESC
                LIMIT 1
            """),
            {"email": email}
        ).mappings().first()
        
        if briefing_row:
            return {
                "ok": True,
                "briefing": {
                    "id": briefing_row["id"],
                    "lang": briefing_row["lang"],
                    "answers": briefing_row["answers"],
                    "created_at": briefing_row["created_at"].isoformat() if briefing_row["created_at"] else None,
                    "type": "final"
                }
            }
        
        # 2. Falls kein Briefing: Draft zurückgeben
        _ensure_drafts_table(db)
        draft_row = db.execute(
            text("""
                SELECT id, email, lang, payload, updated_at 
                FROM briefing_drafts 
                WHERE LOWER(email) = LOWER(:email)
                ORDER BY updated_at DESC 
                LIMIT 1
            """),
            {"email": email}
        ).mappings().first()
        
        if draft_row:
            return {
                "ok": True,
                "briefing": {
                    "id": draft_row["id"],
                    "lang": draft_row["lang"],
                    "answers": draft_row["payload"],
                    "updated_at": draft_row["updated_at"].isoformat() if draft_row["updated_at"] else None,
                    "type": "draft"
                }
            }
        
        return {"ok": True, "briefing": None}
        
    except Exception as exc:
        log.exception("get_my_latest failed: %s", exc)
        raise HTTPException(status_code=500, detail="load_failed")


@router.post("/submit", status_code=202)  # Alias für /briefing_async
@router.post("", status_code=202)  # REST-konform: POST /briefings
def submit_briefing(
    payload: BriefingSubmit,
    background: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_session),
):
    """
    Finalisiert ein Briefing und startet die Analyse im Hintergrund.
    
    Returns:
        202 Accepted mit briefing_id und queued-Status
    """
    user = _get_current_user_safe(request)
    email = _infer_email({"email": payload.email, "answers": payload.answers}, user)
    
    if not email:
        raise HTTPException(status_code=400, detail="email_required")
    
    if not payload.answers:
        raise HTTPException(status_code=422, detail="answers_required")
    
    try:
        # 1. Erstelle finales Briefing
        user_obj = None
        if user and user.get("id"):
            user_obj = db.get(User, user["id"])
        elif email:
            # Versuche User per Email zu finden oder erstellen
            user_obj = db.execute(
                text("SELECT * FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1"),
                {"email": email}
            ).mappings().first()
            
            if not user_obj:
                # Erstelle User
                result = db.execute(
                    text("""
                        INSERT INTO users (email, created_at) 
                        VALUES (:email, now()) 
                        RETURNING id
                    """),
                    {"email": email}
                )
                user_id = result.scalar()
                db.commit()
                user_obj = db.get(User, user_id)
        
        briefing = Briefing(
            user_id=user_obj.id if user_obj else None,
            lang=payload.lang,
            answers=payload.answers,
            created_at=datetime.now(timezone.utc)
        )
        db.add(briefing)
        db.commit()
        db.refresh(briefing)
        
        log.info("Briefing created: id=%s, user_id=%s, email=%s", 
                 briefing.id, briefing.user_id, email)
        
        # 2. Lösche Draft (optional)
        try:
            _ensure_drafts_table(db)
            db.execute(
                text("DELETE FROM briefing_drafts WHERE LOWER(email) = LOWER(:email)"),
                {"email": email}
            )
            db.commit()
        except Exception as e:
            log.warning("Draft cleanup failed (non-critical): %s", e)
        
        # 3. Starte Analyse im Hintergrund
        queued = _start_async_analysis(background, briefing.id, email)
        
        return {
            "ok": True,
            "briefing_id": briefing.id,
            "lang": briefing.lang,
            "queued": queued,
            "message": "Briefing erstellt. Analyse läuft im Hintergrund." if queued 
                      else "Briefing erstellt. Analyse muss manuell gestartet werden."
        }
        
    except Exception as exc:
        log.exception("submit_briefing failed: %s", exc)
        db.rollback()
        raise HTTPException(status_code=500, detail="submission_failed")


# Legacy-Alias für Abwärtskompatibilität
@router.post("/async", status_code=202, include_in_schema=False)
def briefing_async_legacy(
    payload: Dict[str, Any],
    background: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_session),
):
    """Legacy endpoint - weitergeleitet an submit_briefing"""
    # Konvertiere altes Format zu neuem
    answers = payload.get("answers", {})
    if not answers:
        # Fallback: alle Nicht-Meta-Keys sind answers
        meta_keys = {"lang", "email", "to"}
        answers = {k: v for k, v in payload.items() if k not in meta_keys}
    
    submit_payload = BriefingSubmit(
        lang=payload.get("lang", "de"),
        email=payload.get("email") or payload.get("to"),
        answers=answers
    )
    
    return submit_briefing(submit_payload, background, request, db)
