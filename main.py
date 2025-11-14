# -*- coding: utf-8 -*-
"""
main.py — Zentrales FastAPI-Entry‑Point (Gold‑Standard+)

• Robuste CORS‑Konfiguration aus settings.py
• Saubere Router‑Registrierung (auth, briefings, analyze, report, smoke)
• Health-/Info‑Endpunkte und /api/router-status Übersicht
• Defensiver Import: Router werden nur gemountet, wenn Modul vorhanden ist

Dieses File ist bewusst schlank gehalten und enthält keine Projektlogik.
"""
from __future__ import annotations

import importlib
import logging
import os
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

try:
    # Projektweite Settings (Pydantic Settings). Muss ein "settings = Settings()" enthalten.
    from settings import settings
except Exception as exc:  # pragma: no cover
    raise RuntimeError("settings.py mit 'settings = Settings()' wird benötigt.") from exc


# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
LOG_LEVEL = (os.getenv("LOG_LEVEL") or "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("backend.main")


# ----------------------------------------------------------------------------
# App-Initialisierung
# ----------------------------------------------------------------------------
app = FastAPI(
    title="KI Status Report API",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ----------------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------------
if settings.cors_allow_any:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log.info("CORS: allow_any=true (ENV!=production oder CORS_ALLOW_ANY=1)")
else:
    origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log.info("CORS: eingeschränkt auf %s", origins)


# ----------------------------------------------------------------------------
# Hilfsfunktionen: Router aufnehmen, wenn vorhanden
# ----------------------------------------------------------------------------
def try_include(router_module: str, router_attr: str, prefix: str, tags: List[str]) -> bool:
    """
    Importiert dynamisch ein Router-Modul und mountet es, wenn vorhanden.

    Args:
        router_module: Python-Importpfad, z.B. 'routes.auth'
        router_attr:   Attributname des APIRouter-Objekts innerhalb des Moduls
        prefix:        API-Präfix, z.B. '/api/auth'
        tags:          Tag-Liste für OpenAPI

    Returns:
        True, wenn der Router gemountet wurde, sonst False.
    """
    try:
        mod = importlib.import_module(router_module)
        router = getattr(mod, router_attr, None)
        if router is None:
            log.warning("Router '%s.%s' nicht gefunden.", router_module, router_attr)
            return False
        app.include_router(router, prefix=prefix, tags=tags)
        log.info("Router gemountet: %s -> %s", router_module, prefix)
        return True
    except ModuleNotFoundError:
        log.info("Optionaler Router nicht vorhanden: %s", router_module)
        return False
    except Exception as exc:  # pragma: no cover
        log.exception("Fehler beim Registrieren von %s: %s", router_module, exc)
        return False


mounted: Dict[str, bool] = {
    "auth":     try_include("routes.auth", "router", "/api/auth", ["auth"]),
    "briefings":try_include("routes.briefings", "router", "/api/briefings", ["briefings"]),
    "analyze":  try_include("routes.analyze", "router", "/api/analyze", ["analyze"]),
    "report":   try_include("routes.report", "router", "/api/report", ["report"]),
    "smoke":    try_include("routes.smoke", "router", "/api", ["smoke"]),
}


# ----------------------------------------------------------------------------
# Health / Info
# ----------------------------------------------------------------------------
@app.get("/api/healthz", tags=["meta"])
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "healthy": True})

@app.get("/api/info", tags=["meta"])
def info() -> JSONResponse:
    return JSONResponse({
        "name": "KI Status Report API",
        "version": "1.2.1-debug",  # Geändert um Deployment zu verifizieren
        "git_commit": "bce996f",   # Letzter Commit mit Debug-Code
        "status": "running",
        "endpoints": {
            "health": "/api/healthz",
            "auth": "/api/auth/request-code (POST), /api/auth/login (POST)" if mounted.get("auth") else None,
            "briefings": "/api/briefings/submit (POST)" if mounted.get("briefings") else None,
            "report": "/api/report (POST)" if mounted.get("report") else None,
            "smoke": "/api/smoke" if mounted.get("smoke") else None,
        },
    })


@app.get("/api/router-status", tags=["meta"])
def router_status() -> JSONResponse:
    paths = []
    for route in app.router.routes:
        if getattr(route, "path", None):
            paths.append(route.path)
    return JSONResponse({
        "routers": mounted,
        "paths": paths,
        "analyzer_import_ok": bool(mounted.get("analyze")),
        "version": "1.2.0",
    })


# Root: kleine Übersicht (nützlich für Railway Ping)
@app.get("/", include_in_schema=False)
def root() -> JSONResponse:
    paths = []
    for route in app.router.routes:
        if getattr(route, "path", None):
            paths.append(route.path)
    return JSONResponse({
        "name": "KI Status Report API",
        "version": "1.2.0",
        "status": "running",
        "endpoints": {
            "health": "/api/healthz",
            "auth": "/api/auth/request-code (POST), /api/auth/login (POST)" if mounted.get("auth") else None,
            "briefings": "/api/briefings/submit (POST)" if mounted.get("briefings") else None,
            "report": "/api/report (POST)" if mounted.get("report") else None,
            "smoke": "/api/smoke" if mounted.get("smoke") else None,
        },
        "mounted_paths": paths,
    })


# lokaler Start:  uvicorn main:app --reload
if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=bool(os.getenv("DEV_RELOAD", "0") == "1"),
        log_level=LOG_LEVEL.lower(),
    )
