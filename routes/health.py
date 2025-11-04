# file: routes/health.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Health/Status Endpoints
- GET /api/router-status: montierte Router + Analyzer-Importstatus
- GET /api/healthz: ok + version
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request
from settings import settings

router = APIRouter(prefix="/api", tags=["health"])

def _mounted_map(request: Request) -> Dict[str, bool]:
    # why: echte Mount-Prüfung gegen die App-Routen, nicht nur Import
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
        import importlib
        importlib.import_module("gpt_analyze")
        analyzer_ok = True
    except Exception:
        analyzer_ok = False
    return {
        "time": datetime.utcnow().isoformat() + "Z",
        "version": getattr(settings, "VERSION", "1.0.0"),
        "routers": _mounted_map(request),
        "analyzer_import_ok": analyzer_ok,
    }

@router.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "version": getattr(settings, "VERSION", "1.0.0")}
