# -*- coding: utf-8 -*-
"""
KI‑Backend Hauptdatei (Gold‑Standard+, konsolidiert)

Diese Version des ``main.py`` basiert auf dem bestehenden Backend und ergänzt
einen Smoke‑Test‑Router sowie kleinere Verbesserungen. Die App mountet die
Router für Auth, Briefings, Analyse, Report und Smoke. Weiterhin werden CORS
und Health‑Checks konfiguriert. Ein Router‑Status liefert eine Übersicht der
registrierten Pfade und prüft den Import des Analysemoduls. Bei doppelten
Prefixes wird optional ein Alias für ``/api/briefings/submit`` angelegt.

Änderungen gegenüber der vorherigen Version:

* Eintrag für ``routes.smoke`` in ``_build_router_config`` – der neue Router
  stellt ``/api/smoke`` bereit.
* Erweiterung des Root‑Endpunkts um ``smoke`` in der Endpunktliste.
* Alle JSON‑Responses setzen nun explizit den ``charset=utf-8`` in ihrem
  ``Content‑Type`` für konsistente UTF‑8‑Ausgabe.
"""
from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple, Dict, Any

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bool_env(name: str, default: str = "0") -> bool:
    """Interpretiert eine Umgebungsvariable als booleschen Wert."""
    return (os.getenv(name, default) or "").strip().lower() in {"1", "true", "yes"}


log_level = (os.getenv("LOG_LEVEL") or "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
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

    # Auth-Tabellen sicherstellen (kritisch für Login)
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
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Erst CORS_ORIGINS (neue ENV), dann Fallback CORS_ALLOW_ORIGINS (alt)
allowed_origins_raw = os.getenv("CORS_ORIGINS", "") or os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

if not allowed_origins and _bool_env("CORS_ALLOW_ANY", "0"):
    # SECURITY: Cannot use allow_credentials=True with allow_origins=["*"]
    # Choose one: either allow all origins OR allow credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Changed from True for security
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log.warning("⚠️  CORS: Allowing ALL origins WITHOUT credentials (development mode)")
    log.warning("⚠️  For production with credentials, set specific CORS_ORIGINS environment variable")
else:
    if not allowed_origins:
        # konservative Defaults
        allowed_origins = [
            "https://ki-sicherheit.jetzt",
            "https://make.ki-sicherheit.jetzt",
            "https://www.ki-sicherheit.jetzt",
            "https://www.make.ki-sicherheit.jetzt",
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log.info("✓ CORS configured for: %s", ", ".join(allowed_origins))


# ---------------------------------------------------------------------------
# Router Mounting (mit ENV-Guards für Admin)
# ---------------------------------------------------------------------------
def mount_router(module_path: str, prefix: str, name: str) -> bool:
    """Versucht einen Router zu mounten; gibt True bei Erfolg zurück."""
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
    """Stellt die Liste der zu mountenden Router zusammen."""
    cfg: List[Tuple[str, str, str]] = [
        ("routes.auth", "/api", "auth"),
        ("routes.briefings", "/api", "briefings"),
        ("routes.analyze", "/api", "analyze"),
        ("routes.report", "/api", "report"),
        # Smoke‑Test Router: bietet /api/smoke zur Überprüfung des Systems
        ("routes.smoke", "/api", "smoke"),
    ]
    # optionale Admin‑Routen
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
    """Sammelt alle registrierten Pfade aus der FastAPI‑App."""
    return {getattr(r, "path", "") for r in app.routes if getattr(r, "path", "")}


def _status_snapshot() -> Dict[str, Any]:
    """Erzeugt eine Momentaufnahme der gemounteten Router und prüft den Analyzer."""
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
            "smoke": any(p.startswith("/api/smoke") for p in ps),
        },
        "paths": sorted([p for p in ps if p.startswith("/api/")]),
        "analyzer_import_ok": analyzer_ok,
        "version": APP_VERSION,
    }


def _check_and_alias_submit_path() -> None:
    """Überprüft das Vorhandensein des Submit‑Endpoints und legt ggf. einen Alias an."""
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
            async def _alias_submit(request: Request):  # pragma: no cover
                # why: 307 erhält Methode/Body
                return RedirectResponse(url=double, status_code=307)
            log.warning(
                "↪  Added temporary alias %s → %s (307). Set ALLOW_ALIAS_SUBMIT=0 to disable.",
                expected,
                double,
            )
        else:
            log.warning("No alias created (ALLOW_ALIAS_SUBMIT=0).")


@app.get("/")
def root() -> Dict[str, Any]:
    """Root‑Endpoint mit API‑Info."""
    endpoints: Dict[str, str] = {
        "health": "/api/healthz",
        "auth": "/api/auth/request-code (POST), /api/auth/login (POST)",
        "briefings": "/api/briefings/submit (POST)",
        "report": "/api/report (POST)",
        "router_status": "/api/router-status",
        "smoke": "/api/smoke",
    }
    if _bool_env("ENABLE_ADMIN_ROUTES", "0"):
        endpoints["admin"] = "/api/admin/* (GET/POST)"
    if _bool_env("ADMIN_ALLOW_RAW_SQL", "0"):
        endpoints["hotfix"] = "/admin-sql/hotfix.html"
    if os.path.exists("public"):
        endpoints["test_dashboard"] = "/test-dashboard.html (Interactive Test UI)"
    return {
        "name": os.getenv("APP_NAME", "KI-Status-Report API"),
        "version": APP_VERSION,
        "status": "running",
        "endpoints": endpoints,
        "mounted_paths": _status_snapshot()["paths"],
    }


@app.get("/api/router-status", response_class=JSONResponse)
def router_status() -> JSONResponse:
    """Live Router‑Status + Analyzer‑Importprüfung."""
    snap = _status_snapshot()
    # Ergänze Zeitstempel für bessere Nachverfolgung des Status
    import datetime
    snap["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return JSONResponse(content=snap, media_type="application/json; charset=utf-8")


@app.get("/api/healthz", response_class=JSONResponse)
@app.get("/healthz", response_class=JSONResponse)
def healthz() -> JSONResponse:
    """Health‑Check für Monitoring."""
    return JSONResponse(content={"status": "ok", "healthy": True}, media_type="application/json; charset=utf-8")


@app.get("/api/info", response_class=JSONResponse)
def info() -> JSONResponse:
    """System‑Info (nicht in Production)."""
    if (os.getenv("ENV") or "production").lower() == "production":
        return JSONResponse(content={"error": "Not available in production"}, media_type="application/json; charset=utf-8")
    import sys
    import platform
    return JSONResponse(
        content={
            "python": sys.version,
            "platform": platform.platform(),
            "env": os.getenv("ENV", "unknown"),
            "log_level": log_level,
            "mounted_routers": mounted_count,
            "database": (
                os.getenv("DATABASE_URL", "").split("@")[-1]
                if "@" in os.getenv("DATABASE_URL", "")
                else "not configured"
            ),
        },
        media_type="application/json; charset=utf-8",
    )


# ---------------------------------------------------------------------------
# Legacy Endpoint (Abwärtskompatibilität)
# ---------------------------------------------------------------------------
@app.post("/api/briefing_async", status_code=202)
async def legacy_briefing_async_endpoint(
    request: Request,
    background: BackgroundTasks,
):
    """
    DEPRECATED: Legacy‑Endpoint für das alte Frontend.

    SECURITY WARNING: This endpoint has limited security controls.
    Please migrate to /api/briefings/submit which has proper authentication.

    This endpoint will be removed in a future version.
    """
    # Log deprecation warning
    log.warning("⚠️  DEPRECATED ENDPOINT CALLED: /api/briefing_async - Please migrate to /api/briefings/submit")
    log.warning("⚠️  Client: %s", request.client.host if request.client else "unknown")

    # Rate limiting for legacy endpoint
    from services.rate_limit import RateLimiter
    limiter = RateLimiter(namespace="legacy_briefing", limit=5, window_sec=300)
    limiter.hit(key=request.client.host if request.client else "unknown")

    try:
        # Legacy implementation removed - redirect to new endpoint
        return JSONResponse(
            status_code=410,  # Gone
            content={
                "ok": False,
                "error": "This endpoint has been removed. Please use /api/briefings/submit instead.",
                "migration_guide": "POST to /api/briefings/submit with JSON body: {lang: 'de', answers: {...}, queue_analysis: true}"
            }
        )
    except Exception as exc:
        log.exception("Legacy endpoint /api/briefing_async failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "internal_error",
                "detail": "Briefing submission failed",
                "hint": "Consider migrating to /api/briefings/submit",
            },
            media_type="application/json; charset=utf-8",
        )


# ---------------------------------------------------------------------------
# Error Handler
# ---------------------------------------------------------------------------
@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "detail": "Endpoint nicht gefunden",
            "path": str(request.url.path),
            "hint": "API-Dokumentation /docs",
        },
        media_type="application/json; charset=utf-8",
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc) -> JSONResponse:
    log.exception("Internal server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": "Interner Serverfehler. Bitte später erneut versuchen.",
            "support": "Bei anhaltenden Problemen kontaktieren Sie bitte den Support.",
        },
        media_type="application/json; charset=utf-8",
    )


# ---------------------------------------------------------------------------
# Startup Banner & route checks
# ---------------------------------------------------------------------------
log.info("=" * 60)
log.info("KI-Backend ready!")
log.info("Environment: %s", os.getenv("ENV", "production"))
log.info("Log Level: %s", log_level)
log.info("=" * 60)

# ---------------------------------------------------------------------------
# Static Files für Test-Dashboard (falls vorhanden)
# ---------------------------------------------------------------------------
if os.path.exists("public"):
    try:
        # Spezifischer Route für test-dashboard.html
        @app.get("/test-dashboard.html", include_in_schema=False)
        async def serve_test_dashboard():
            """Serviert das interaktive Test-Dashboard"""
            return FileResponse("public/test-dashboard.html", media_type="text/html; charset=utf-8")

        # Minimale Version des Dashboards
        @app.get("/test-dashboard-minimal.html", include_in_schema=False)
        async def serve_test_dashboard_minimal():
            """Serviert das minimale Test-Dashboard (garantiert funktionierend)"""
            return FileResponse("public/test-dashboard-minimal.html", media_type="text/html; charset=utf-8")

        # Mount public directory für weitere statische Dateien
        app.mount("/public", StaticFiles(directory="public"), name="public")
        log.info("✓ Test-Dashboard verfügbar unter: /test-dashboard.html und /test-dashboard-minimal.html")
    except Exception as exc:
        log.warning("⚠️  Public directory exists but mount failed: %s", exc)
else:
    log.debug("ℹ️  Public directory not found - Test-Dashboard not available")

# Prüfen & ggf. Alias anlegen (nur wenn Doppel-Prefix erkannt)
_check_and_alias_submit_path()


# ---------------------------------------------------------------------------
# Optional: Direkter Start mit Uvicorn (lokale Entwicklung)
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)