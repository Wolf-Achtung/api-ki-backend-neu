# file: routes/health.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Health/Status – wird in main unter /api gemountet."""
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Request
from settings import settings

router = APIRouter(tags=["health"])

def _mounted_map(request: Request) -> Dict[str, bool]:
    paths = {getattr(r, "path", "") for r in request.app.routes}
    return {
        "auth": any(p.startswith("/api/auth") for p in paths),
        "briefings": any(p.startswith("/api/briefings") for p in paths),
        "analyze": any(p.startswith("/api/analyze") for p in paths),
        "report": any(p.startswith("/api/report") for p in paths),
    }

@router.get("/router-status")
def router_status(request: Request) -> Dict[str, Any]:
    try:
        import importlib; importlib.import_module("gpt_analyze")
        analyzer_ok = True
    except Exception:
        analyzer_ok = False
    return {
        "time": datetime.utcnow().isoformat() + "Z",
        "version": getattr(settings, "VERSION", "1.2.0"),
        "routers": _mounted_map(request),
        "analyzer_import_ok": analyzer_ok,
    }

@router.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "version": getattr(settings, "VERSION", "1.2.0")}
