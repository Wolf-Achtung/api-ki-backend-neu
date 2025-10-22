# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from gpt_analyze import build_report

router = APIRouter()

@router.post("/analyze")
async def analyze(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Runs the full HTML report generation based on the questionnaire payload.
    Returns HTML + meta (scores, badge, critical fields, etc.).
    """
    try:
        lang = str(payload.get("lang", "de")).lower()
        result = build_report(payload, lang=lang)
        return {"ok": True, **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {exc}")
