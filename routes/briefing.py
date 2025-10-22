# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from typing import Any, Dict, Optional
from uuid import uuid4

router = APIRouter()

@router.post("/briefing_async")
async def briefing_async(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Receives the questionnaire payload (flat keys as sent by the Formbuilder).
    Returns an acknowledgement and echoes minimal metadata.
    The actual analysis is handled via /api/analyze.
    """
    lang = str(payload.get("lang", "de")).lower()
    email = payload.get("email") or payload.get("to")
    receipt = f"recv_{uuid4().hex[:16]}"
    # Minimal validation – always accept for now (frontend validates required fields)
    return {
        "ok": True,
        "receipt": receipt,
        "lang": lang,
        "email": email,
        "received_keys": sorted(list(payload.keys())),
    }
