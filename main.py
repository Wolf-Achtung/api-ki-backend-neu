# -*- coding: utf-8 -*-
"""
KI-Backend Hauptdatei mit robustem Router-Mounting und Startup-Checks.
Version 1.2.0 - Aenderungen:
- Admin-Router werden nur geladen, wenn per ENV freigeschaltet (ENABLE_ADMIN_ROUTES / ADMIN_ALLOW_RAW_SQL).
- CORS liest jetzt **CORS_ORIGINS** (neu) und faellt zurueck auf **CORS_ALLOW_ORIGINS** (alt).
- Besseres Logging der Router-Summary.
- Optionaler __main__-Block fuer lokale Starts (PORT aus ENV).
"""
from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request, BackgroundTasks

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _bool_env(name: str, default: str = "0") -> bool:
    return (os.getenv(name, default) or "").strip() in {"1", "true", "True", "YES", "yes"}

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
app = FastAPI(
    title=os.getenv("APP_NAME", "KI-Status-Report API"),
    version="1.2.0",
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
    """Liste der zu mountenden Router; Admin nur bei Freigabe."""
    cfg: List[Tuple[str, str, str]] = [
        ("routes.auth", "/api", "auth"),
        ("routes.briefings", "/api", "briefings"),
        ("routes.analyze", "/api", "analyze"),
        ("routes.report", "/api", "report"),
    ]
    if _bool_env("ENABLE_ADMIN_ROUTES", "0"):
        cfg.append(("routes.admin", "/api", "admin"))
    # Raw-SQL nur, wenn explizit erlaubt
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
# Health / Root / Info
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """Root endpoint mit API-Info"""
    endpoints = {
        "health": "/api/healthz",
        "auth": "/api/auth/request-code (POST), /api/auth/login (POST)",
        "briefings": "/api/briefings/* (GET/PUT/POST/DELETE)",
        "report": "/api/report (POST)",
    }
    if _bool_env("ENABLE_ADMIN_ROUTES", "0"):
        endpoints["admin"] = "/api/admin/* (GET/POST)"
    if _bool_env("ADMIN_ALLOW_RAW_SQL", "0"):
        endpoints["hotfix"] = "/admin-sql/hotfix.html"

    return {
        "name": os.getenv("APP_NAME", "KI-Status-Report API"),
        "version": "1.2.0",
        "status": "running",
        "endpoints": endpoints
    }


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
# Startup Banner
# ---------------------------------------------------------------------------
log.info("=" * 60)
log.info("KI-Backend ready!")
log.info("Environment: %s", os.getenv("ENV", "production"))
log.info("Log Level: %s", log_level)
log.info("=" * 60)


# ---------------------------------------------------------------------------
# Optional: Direkter Start mit Uvicorn (lokale Entwicklung)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
