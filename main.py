# -*- coding: utf-8 -*-
"""
KI-Backend Hauptdatei (Gold‑Standard+, konsolidiert)
- Bewahrt alle bisherigen Features (Lifespan, CORS mit ENV, Admin-Guards, Legacy-Endpunkt, Fehlerhandler).
- Neu: /api/router-status (zeigt montierte Router + Pfade + Analyzer-Import).
- Neu: Start‑Zeitprüfung, ob /api/briefings/submit existiert; Warnung bei Doppel-Prefix.
- Optional: Alias-Fix bei Doppel-Prefix (env ALLOW_ALIAS_SUBMIT=1 → legt /api/briefings/submit mit 307-Redirect an).
"""
from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple, Dict, Any

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bool_env(name: str, default: str = "0") -> bool:
    return (os.getenv(name, default) or "").strip().lower() in {"1", "true", "yes"}

log_level = (os.getenv("LOG_LEVEL") or "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("ki-backend")


# ---------------------------------------------------------------------------
# Lifespan & Startup Checks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("=" * 60)
    log.info("Starting KI-Backend...")
    log.info("=" * 60)

    # Auth-Tabellen sicherstellen (kritisch fuer Login)
    try:
        from core.db import SessionLocal
        from services.auth import _ensure_login_codes_table
        db = SessionLocal()
        try:
            _ensure_login_codes_table(db)
            log.info("✓ Login-codes table ready")
        except Exception as auth_exc:
            log.error("✗ Login-codes table setup failed: %s", auth_exc)
            log.error("⚠️  LOGIN WILL NOT WORK - Apply hotfix via /admin-sql/hotfix.html")
        finally:
            db.close()
    except Exception as exc:
        log.error("✗ Auth setup failed: %s", exc)
        log.error("⚠️  LOGIN WILL NOT WORK - Check database connection")

    yield

    log.info("Shutting down KI-Backend...")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
APP_VERSION = os.getenv("APP_VERSION", "1.2.0")
app = FastAPI(
    title=os.getenv("APP_NAME", "KI-Status-Report API"),
    version=APP_VERSION,
    description="Backend fuer KI-Readiness Assessments",
    lifespan=lifespan
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# NEU: erst CORS_ORIGINS (neue ENV), dann Fallback CORS_ALLOW_ORIGINS (alt)
allowed_origins_raw = os.getenv("CORS_ORIGINS", "") or os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

if not allowed_origins and _bool_env("CORS_ALLOW_ANY", "0"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    log.warning("⚠️  CORS: Allowing ALL origins (development mode)")
else:
    if not allowed_origins:
        # konservative Defaults
        allowed_origins = [
            "https://ki-sicherheit.jetzt",
            "https://make.ki-sicherheit.jetzt",
            "https://www.ki-sicherheit.jetzt",
            "https://www.make.ki-sicherheit.jetzt"
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    log.info("✓ CORS configured for: %s", ", ".join(allowed_origins))


# ---------------------------------------------------------------------------
# Router Mounting (mit ENV-Guards fuer Admin)
# ---------------------------------------------------------------------------
def mount_router(module_path: str, prefix: str, name: str) -> bool:
    """Versucht einen Router zu mounten; gibt True bei Erfolg zurueck."""
    try:
        parts = module_path.split(".")
        module = __import__(module_path, fromlist=[parts[-1]])
        if not hasattr(module, "router"):
            log.error("✗ Module %s has no 'router' attribute", module_path)
            return False
        app.include_router(getattr(module, "router"), prefix=prefix)
        full_path = f"{prefix}/{name}".rstrip("/")
        log.info("✓ Mounted: %s -> %s", module_path, full_path)
        return True
    except ImportError as exc:
        log.error("✗ Import failed for %s: %s", module_path, exc)
        return False
    except Exception as exc:
        log.error("✗ Mount failed for %s: %s", module_path, exc)
        return False


def _build_router_config() -> List[Tuple[str, str, str]]:
    cfg: List[Tuple[str, str, str]] = [
        ("routes.auth", "/api", "auth"),
        ("routes.briefings", "/api", "briefings"),
        ("routes.analyze", "/api", "analyze"),
        ("routes.report", "/api", "report"),
    ]
    if _bool_env("ENABLE_ADMIN_ROUTES", "0"):
        cfg.append(("routes.admin", "/api", "admin"))
    if _bool_env("ADMIN_ALLOW_RAW_SQL", "0"):
        cfg.append(("routes.admin_sql", "", "admin-sql"))
    return cfg


routers_config = _build_router_config()
mounted_count = 0
failed_routers: List[str] = []

for module_path, prefix, name in routers_config:
    if mount_router(module_path, prefix, name):
        mounted_count += 1
    else:
        failed_routers.append(name)

log.info("-" * 60)
log.info("Router Summary: %d/%d mounted successfully", mounted_count, len(routers_config))
if failed_routers:
    log.warning("⚠️  Failed routers: %s", ", ".join(failed_routers))
    if "auth" in failed_routers:
        log.error("⌧ CRITICAL: Auth router failed - LOGIN WILL NOT WORK")
else:
    log.info("✓ All routers mounted successfully!")
log.info("-" * 60)


# ---------------------------------------------------------------------------
# Health / Root / Info / Router-Status
# ---------------------------------------------------------------------------
def _paths_set() -> set[str]:
    return {getattr(r, "path", "") for r in app.routes if getattr(r, "path", "")}

def _status_snapshot() -> Dict[str, Any]:
    ps = _paths_set()
    try:
        import importlib
        importlib.import_module("gpt_analyze")
        analyzer_ok = True
    except Exception:
        analyzer_ok = False
    return {
        "routers": {
            "auth": any(p.startswith("/api/auth") for p in ps),
            "briefings": any(p.startswith("/api/briefings") for p in ps),
            "analyze": any(p.startswith("/api/analyze") for p in ps),
            "report": any(p.startswith("/api/report") for p in ps),
        },
        "paths": sorted([p for p in ps if p.startswith("/api/")]),
        "analyzer_import_ok": analyzer_ok,
        "version": APP_VERSION,
    }

def _check_and_alias_submit_path() -> None:
    ps = _paths_set()
    expected = "/api/briefings/submit"
    double = "/api/api/briefings/submit"
    has_expected = expected in ps
    has_double = double in ps
    if has_expected:
        log.info("✓ Endpoint present: %s", expected)
        return
    if has_double:
        log.warning("⚠️  Detected double prefix route: %s", double)
        if _bool_env("ALLOW_ALIAS_SUBMIT", "1"):
            @app.post(expected)
            async def _alias_submit(request: Request):
                # why: 307 erhält Methode/Body
                return RedirectResponse(url=double, status_code=307)
            log.warning("↪  Added temporary alias %s → %s (307). Set ALLOW_ALIAS_SUBMIT=0 to disable.", expected, double)
        else:
            log.warning("No alias created (ALLOW_ALIAS_SUBMIT=0).")


@app.get("/")
def root():
    """Root endpoint mit API-Info"""
    endpoints = {
        "health": "/api/healthz",
        "auth": "/api/auth/request-code (POST), /api/auth/login (POST)",
        "briefings": "/api/briefings/submit (POST)",
        "report": "/api/report (POST)",
        "router_status": "/api/router-status",
    }
    if _bool_env("ENABLE_ADMIN_ROUTES", "0"):
        endpoints["admin"] = "/api/admin/* (GET/POST)"
    if _bool_env("ADMIN_ALLOW_RAW_SQL", "0"):
        endpoints["hotfix"] = "/admin-sql/hotfix.html"

    return {
        "name": os.getenv("APP_NAME", "KI-Status-Report API"),
        "version": APP_VERSION,
        "status": "running",
        "endpoints": endpoints,
        "mounted_paths": _status_snapshot()["paths"],
    }


@app.get("/api/router-status")
def router_status():
    """Live Router-Status + Analyzer-Importprüfung"""
    return _status_snapshot()


@app.get("/api/healthz")
@app.get("/healthz")
def healthz():
    """Health check fuer Monitoring"""
    return {"status": "ok", "healthy": True}


@app.get("/api/info")
def info():
    """System-Info (nicht in Production)"""
    if (os.getenv("ENV") or "production").lower() == "production":
        return {"error": "Not available in production"}
    import sys, platform
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "env": os.getenv("ENV", "unknown"),
        "log_level": log_level,
        "mounted_routers": mounted_count,
        "database": (os.getenv("DATABASE_URL", "").split("@")[-1] if "@" in os.getenv("DATABASE_URL", "") else "not configured")
    }


# ---------------------------------------------------------------------------
# Legacy Endpoint (Abwaertskompatibilitaet)
# ---------------------------------------------------------------------------
@app.post("/api/briefing_async", status_code=202)
async def legacy_briefing_async_endpoint(
    request: Request,
    background: BackgroundTasks,
):
    """
    Legacy-Endpoint fuer altes Frontend. Leitet an /api/briefings/async weiter.
    Bitte auf /api/briefings/submit umstellen.
    """
    try:
        from routes.briefings import briefing_async_legacy
        from core.db import SessionLocal

        body = await request.json()
        db = SessionLocal()
        try:
            return briefing_async_legacy(body, background, request, db)
        finally:
            db.close()
    except Exception as exc:
        log.exception("Legacy endpoint /api/briefing_async failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "internal_error",
                "detail": "Briefing submission failed",
                "hint": "Consider migrating to /api/briefings/submit"
            }
        )


# ---------------------------------------------------------------------------
# Error Handler
# ---------------------------------------------------------------------------
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "detail": "Endpoint nicht gefunden",
            "path": str(request.url.path),
            "hint": "API-Dokumentation /docs"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    log.exception("Internal server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": "Interner Serverfehler. Bitte spaeter erneut versuchen.",
            "support": "Bei anhaltenden Problemen kontaktieren Sie bitte den Support."
        }
    )


# ---------------------------------------------------------------------------
# Startup Banner & route checks
# ---------------------------------------------------------------------------
log.info("=" * 60)
log.info("KI-Backend ready!")
log.info("Environment: %s", os.getenv("ENV", "production"))
log.info("Log Level: %s", log_level)
log.info("=" * 60)

# Prüfen & ggf. Alias anlegen (nur wenn Doppel-Prefix erkannt)
_check_and_alias_submit_path()


# ---------------------------------------------------------------------------
# Optional: Direkter Start mit Uvicorn (lokale Entwicklung)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
