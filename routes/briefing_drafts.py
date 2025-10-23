# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import logging, json

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import get_session, engine
from services.auth import get_current_user
from models import Briefing, User

log = logging.getLogger("routes.briefing_drafts")
router = APIRouter(tags=["briefing-drafts"])

DDL_CREATE = """
CREATE TABLE IF NOT EXISTS briefing_drafts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    lang VARCHAR(5) NOT NULL DEFAULT 'de',
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, lang)
);
"""

@router.on_event("startup")
def _ensure_table():
    try:
        with engine.begin() as conn:
            conn.execute(text(DDL_CREATE))
        log.info("briefing_drafts table ready")
    except Exception as exc:
        log.exception("briefing_drafts table init failed: %s", exc)

@router.get("/briefings/me/latest")
def get_latest(db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    br = db.query(Briefing).filter(Briefing.user_id == user.id).order_by(Briefing.id.desc()).first()
    if not br:
        return {"ok": True, "briefing": None}
    return {"ok": True, "briefing": {"id": br.id, "lang": br.lang, "answers": br.answers, "created_at": br.created_at.isoformat()}}

@router.get("/briefings/draft")
def draft_get(user: User = Depends(get_current_user)):
    sql = text("SELECT id, lang, answers, updated_at FROM briefing_drafts WHERE user_id=:uid LIMIT 1")
    with engine.begin() as conn:
        row = conn.execute(sql, {"uid": user.id}).mappings().first()
    if not row:
        return {"ok": True, "draft": None}
    return {"ok": True, "draft": {"id": row["id"], "lang": row["lang"], "answers": row["answers"], "updated_at": row["updated_at"].isoformat()}}

@router.put("/briefings/draft")
def draft_put(payload: Dict[str, Any] = Body(...), user: User = Depends(get_current_user)):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="JSON object expected")
    answers = payload.get("answers") or payload
    lang = (payload.get("lang") or "de").strip().lower()[:5]
    sql = text("""
        INSERT INTO briefing_drafts (user_id, lang, answers, updated_at)
        VALUES (:uid, :lang, CAST(:answers AS JSONB), NOW())
        ON CONFLICT (user_id, lang) DO UPDATE SET answers=EXCLUDED.answers, updated_at=NOW()
        RETURNING id, lang, answers, updated_at
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"uid": user.id, "lang": lang, "answers": json.dumps(answers)}).mappings().first()
    return {"ok": True, "draft": {"id": row["id"], "lang": row["lang"], "answers": row["answers"], "updated_at": row["updated_at"].isoformat()}}

@router.delete("/briefings/draft")
def draft_delete(user: User = Depends(get_current_user)):
    sql = text("DELETE FROM briefing_drafts WHERE user_id=:uid RETURNING id")
    with engine.begin() as conn:
        row = conn.execute(sql, {"uid": user.id}).first()
    return {"ok": True, "deleted": bool(row)}
