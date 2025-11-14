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
        "version": "1.2.0",
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


@app.get("/api/debug/config", tags=["debug"])
def debug_config() -> JSONResponse:
    """Debug endpoint für Konfigurationsinformationen (ohne Secrets)"""
    return JSONResponse({
        "app": {
            "name": settings.app_name,
            "env": settings.env,
            "log_level": settings.log_level,
            "version": "1.2.0",
        },
        "urls": {
            "site_url": settings.site_url,
            "backend_base": settings.backend_base,
        },
        "database": {
            "url_set": bool(settings.database_url),
            "redis_url_set": bool(settings.redis_url),
        },
        "cors": {
            "allow_any": settings.cors_allow_any,
            "origins": settings.cors_origins,
        },
        "features": {
            "enable_llm_cache": settings.enable_llm_cache,
            "enable_perplexity": settings.enable_perplexity,
            "enable_quality_gates": settings.enable_quality_gates,
            "enable_realistic_scores": settings.enable_realistic_scores,
            "enable_ai_act_section": settings.enable_ai_act_section,
            "enable_ai_act_table": settings.enable_ai_act_table,
            "enable_admin_notify": settings.enable_admin_notify,
            "enable_repair_html": settings.enable_repair_html,
        },
        "mail": {
            "provider": settings.mail.provider,
            "from_email": settings.mail.from_email,
            "from_name": settings.mail.from_name,
        },
        "security": {
            "jwt_secret_set": bool(settings.security.jwt_secret),
            "jwt_secret_length": len(settings.security.jwt_secret) if settings.security.jwt_secret else 0,
            "jwt_algorithm": settings.security.jwt_algorithm,
            "jwt_expire_days": settings.security.jwt_expire_days,
        },
        "openai": {
            "api_key_set": bool(settings.openai.api_key),
            "model": settings.openai.model,
            "temperature": settings.openai.temperature,
            "max_tokens": settings.openai.max_tokens,
        },
        "research": {
            "provider": settings.research.provider,
            "lang": settings.research.lang,
            "country": settings.research.country,
        },
    })


@app.get("/api/debug/env", tags=["debug"])
def debug_env() -> JSONResponse:
    """Debug endpoint für wichtige Umgebungsvariablen (ohne Secrets)"""
    env_vars = {}

    # Sichere Env-Vars die keinen Secret enthalten
    safe_vars = [
        "ENV", "LOG_LEVEL", "APP_NAME", "SITE_URL", "BACKEND_BASE",
        "CORS_ALLOW_ANY", "EMAIL_PROVIDER", "RESEARCH_PROVIDER",
        "OPENAI_MODEL", "PERPLEXITY_MODEL", "ENABLE_LLM_CACHE",
        "ENABLE_PERPLEXITY", "ENABLE_QUALITY_GATES",
    ]

    for var in safe_vars:
        value = os.getenv(var)
        if value is not None:
            env_vars[var] = value

    # Secret-Status (nur ob gesetzt, nicht der Wert)
    secrets_status = {}
    secret_vars = [
        "JWT_SECRET", "OPENAI_API_KEY", "PERPLEXITY_API_KEY",
        "TAVILY_API_KEY", "DATABASE_URL", "REDIS_URL",
        "SMTP_PASSWORD",
    ]

    for var in secret_vars:
        value = os.getenv(var)
        secrets_status[var] = {
            "set": bool(value),
            "length": len(value) if value else 0,
        }

    return JSONResponse({
        "environment": env_vars,
        "secrets_status": secrets_status,
    })


@app.get("/api/debug/system", tags=["debug"])
def debug_system() -> JSONResponse:
    """Debug endpoint für System-Informationen"""
    import platform
    import sys

    return JSONResponse({
        "python": {
            "version": sys.version,
            "version_info": {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro,
            },
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "mounted_routers": mounted,
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
