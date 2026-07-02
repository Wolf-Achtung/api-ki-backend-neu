# -*- coding: utf-8 -*-
"""
routes/admin_feedback.py — Admin endpoint to list feedback entries.

Mounted under /api -> /api/admin/feedback
Auth via STRATEGY_ADMIN_KEY query parameter (same key as strategy admin endpoints).
"""
from __future__ import annotations

import hmac
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from routes._bootstrap import get_db

router = APIRouter(prefix="/admin/feedback", tags=["admin-feedback"])
log = logging.getLogger(__name__)

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


def _verify_admin_key(admin_key: str) -> None:
    """Verify admin_key against STRATEGY_ADMIN_KEY env var."""
    expected_key = os.getenv("STRATEGY_ADMIN_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=500, detail="STRATEGY_ADMIN_KEY nicht konfiguriert")
    if not hmac.compare_digest(admin_key or "", expected_key):
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")


@router.get("/list")
def list_feedback(
    admin_key: str = Query(..., description="Admin API Key"),
    type: Optional[str] = Query(None, description="Filter by feedback type (payload->type)"),
    since: Optional[str] = Query(None, description="Filter: created_at >= this date (ISO format, e.g. 2026-03-01)"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max entries to return"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    List all feedback entries, sorted by created_at DESC.

    Supports optional filters:
    - type: filter by payload->'type' value
    - since: only entries created on or after this date
    - limit: max entries (default 100, max 500)
    """
    _verify_admin_key(admin_key)

    # Build query dynamically
    conditions: List[str] = []
    params: Dict[str, Any] = {"lim": limit}

    if type:
        conditions.append("payload->>'type' = :ftype")
        params["ftype"] = type

    if since:
        try:
            datetime.fromisoformat(since)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid 'since' format. Use ISO date, e.g. 2026-03-01")
        conditions.append("created_at >= :since")
        params["since"] = since

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = text(f"""
        SELECT id, payload, source, created_at
        FROM feedbacks
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :lim
    """)

    try:
        rows = db.execute(query, params).fetchall()
    except Exception as exc:
        log.error("Failed to query feedbacks: %s", exc)
        raise HTTPException(status_code=500, detail="Datenbankfehler beim Abrufen der Feedbacks")

    feedback_list = []
    for row in rows:
        payload = row[1] if isinstance(row[1], dict) else {}
        feedback_list.append({
            "id": row[0],
            "email": payload.get("email", payload.get("_meta", {}).get("email", "")),
            "type": payload.get("type", ""),
            "data": payload,
            "created_at": row[3].isoformat() if row[3] else None,
        })

    return {
        "count": len(feedback_list),
        "feedback": feedback_list,
    }
