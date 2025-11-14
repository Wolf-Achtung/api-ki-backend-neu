# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Health/Status & Info Router
- Erkennt Router sowohl mit als auch ohne /api-Prefix (z. B. /auth UND /api/auth)
- Liefert eine saubere /api/info Übersicht OHNE "/api/api"-Dopplungen
- Beinhaltet /api/router-status und /api/healthz
"""
from datetime import datetime
from typing import Any, Dict, List, Set

from fastapi import APIRouter, Request
from fastapi.routing import APIRoute
from settings import settings

router = APIRouter(tags=["health"])


def _mounted_map(request: Request) -> Dict[str, bool]:
    """Erkennt Router auch ohne API-Prefix."""
    paths: Set[str] = {getattr(r, "path", "") for r in request.app.routes if hasattr(r, "path")}
    def _has(prefix: str) -> bool:
        # akzeptiert /api/<prefix> und /<prefix>
        return any(p.startswith(f"/api/{prefix}") or p.startswith(f"/{prefix}") for p in paths)

    return {
        "auth": _has("auth"),
        "briefings": _has("briefings"),
        "analyze": _has("analyze"),
        "report": _has("report"),
    }


def _list_routes(request: Request) -> List[Dict[str, Any]]:
    """Gibt alle APIRoutes mit Methoden zurück (ohne HEAD/OPTIONS)."""
    routes: List[Dict[str, Any]] = []
    for r in request.app.routes:
        if isinstance(r, APIRoute):
            methods = sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"})
            routes.append({"path": r.path, "methods": methods, "name": r.name})
    return routes


def _dedup_paths(routes: List[Dict[str, Any]]) -> List[str]:
    """Dedup der Pfade; gibt die rohen Pfade zurück (keine Präfixe hinzufügen)."""
    uniq = sorted({r["path"] for r in routes})
    return uniq


def _collect_by_prefix(routes: List[Dict[str, Any]], prefix: str) -> List[str]:
    """Erstellt Label-Liste im Format '/path (METHOD[,METHOD])' für einen Prefix (z. B. 'auth')."""
    out: List[str] = []
    for r in routes:
        if r["path"].startswith(f"/api/{prefix}") or r["path"].startswith(f"/{prefix}"):
            if r["methods"]:
                out.append(f'{r["path"]} ({", ".join(sorted(r["methods"]))})')
            else:
                out.append(r["path"])
    return sorted(out)


@router.get("/router-status")
def router_status(request: Request) -> Dict[str, Any]:
    try:
        import importlib; importlib.import_module("gpt_analyze")
        analyzer_ok = True
    except Exception:
        analyzer_ok = False
    return {
        "time": datetime.utcnow().isoformat() + "Z",
        "version": getattr(settings, "VERSION", "1.2.1"),
        "routers": _mounted_map(request),
        "analyzer_import_ok": analyzer_ok,
    }


@router.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "version": getattr(settings, "VERSION", "1.2.1")}


@router.get("/info")
def info(request: Request) -> Dict[str, Any]:
    """Kompakte Service-Übersicht mit deduplizierten Pfaden (keine '/api/api' Dopplungen)."""
    routes = _list_routes(request)
    mounted = _mounted_map(request)

    return {
        "name": "KI Status Report API",
        "version": getattr(settings, "VERSION", "1.2.1"),
        "status": "running",
        "endpoints": {
            "health": "/api/healthz",
            "router_status": "/api/router-status",
            "smoke": "/api/smoke",
            "auth": _collect_by_prefix(routes, "auth"),
            "briefings": _collect_by_prefix(routes, "briefings"),
            "analyze": _collect_by_prefix(routes, "analyze"),
            "report": _collect_by_prefix(routes, "report"),
        },
        "mounted_paths": _dedup_paths(routes),
        "routers": mounted,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }