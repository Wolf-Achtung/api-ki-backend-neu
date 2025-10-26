# -*- coding: utf-8 -*-
"""
KI-Backend Hauptdatei mit robustem Router-Mounting und Startup-Checks.
IMPROVED: Better error handling, non-fatal migrations, clearer logging
"""
from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Logging konfigurieren
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("ki-backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager - führt Startup-Tasks aus (non-fatal errors)"""
    log.info("=" * 60)
    log.info("Starting KI-Backend...")
    log.info("=" * 60)
    
    # Auth-Tabellen sicherstellen (CRITICAL - muss funktionieren)
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
    
    # Shutdown
    log.info("Shutting down KI-Backend...")


# FastAPI App erstellen
app = FastAPI(
    title="KI-Status-Report API",
    version="1.1.1",
    description="Backend für KI-Readiness Assessments",
    lifespan=lifespan
)


# ============================================================================
# CORS Konfiguration
# ============================================================================

allowed_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

if not allowed_origins and os.getenv("CORS_ALLOW_ANY", "0") == "1":
    # Development: Alle Origins erlauben
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    log.warning("⚠️  CORS: Allowing ALL origins (development mode)")
else:
    # Production: Nur spezifische Origins
    if not allowed_origins:
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


# ============================================================================
# Router Mounting
# ============================================================================

def mount_router(module_path: str, prefix: str, name: str) -> bool:
    """
    Versucht einen Router zu mounten.
    
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    try:
        # Dynamischer Import
        parts = module_path.split(".")
        module = __import__(module_path, fromlist=[parts[-1]])
        
        # Router extrahieren
        if not hasattr(module, "router"):
            log.error("✗ Module %s has no 'router' attribute", module_path)
            return False
        
        router = module.router
        
        # In App einbinden
        app.include_router(router, prefix=prefix)
        
        full_path = f"{prefix}/{name}".rstrip("/")
        log.info("✓ Mounted: %s → %s", module_path, full_path)
        return True
        
    except ImportError as exc:
        log.error("✗ Import failed for %s: %s", module_path, exc)
        return False
    except Exception as exc:
        log.error("✗ Mount failed for %s: %s", module_path, exc)
        return False


# Mounted Router (Reihenfolge ist wichtig!)
routers_config = [
    # Auth muss ZUERST geladen werden (Dependency für andere Router)
    ("routes.auth", "/api", "auth"),
    
    # Core-Funktionalität
    ("routes.briefings", "/api", "briefings"),
    ("routes.analyze", "/api", "analyze"),
    ("routes.report", "/api", "report"),
    
    # Admin-Bereich
    ("routes.admin", "/api", "admin"),
    ("routes.admin_sql", "", "admin-sql"),
]

mounted_count = 0
failed_routers = []

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
        log.error("❌ CRITICAL: Auth router failed - LOGIN WILL NOT WORK")
else:
    log.info("✓ All routers mounted successfully!")

log.info("-" * 60)


# ============================================================================
# Health Check & Info Endpoints
# ============================================================================

@app.get("/")
def root():
    """Root endpoint mit API-Info"""
    return {
        "name": "KI-Status-Report API",
        "version": "1.1.1",
        "status": "running",
        "endpoints": {
            "health": "/api/healthz",
            "auth": "/api/auth/request-code (POST), /api/auth/login (POST)",
            "briefings": "/api/briefings/* (GET/PUT/POST/DELETE)",
            "admin": "/api/admin/* (GET/POST)",
            "hotfix": "/admin-sql/hotfix.html (Nur bei DB-Problemen)"
        }
    }


@app.get("/api/healthz")
@app.get("/healthz")
def healthz():
    """Health check für Monitoring"""
    return {"status": "ok", "healthy": True}


@app.get("/api/info")
def info():
    """System-Info (nur Development)"""
    if os.getenv("ENV", "production").lower() == "production":
        return {"error": "Not available in production"}
    
    import sys
    import platform
    
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "env": os.getenv("ENV", "unknown"),
        "log_level": log_level,
        "mounted_routers": mounted_count,
        "database": os.getenv("DATABASE_URL", "").split("@")[-1] if "@" in os.getenv("DATABASE_URL", "") else "not configured"
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 Handler mit Hinweisen"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "detail": "Endpoint nicht gefunden",
            "path": str(request.url.path),
            "hint": "Prüfen Sie die API-Dokumentation unter /docs"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 Handler"""
    log.exception("Internal server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": "Interner Serverfehler. Bitte später erneut versuchen.",
            "support": "Bei anhaltenden Problemen kontaktieren Sie bitte den Support."
        }
    )


# ============================================================================
# Startup Message
# ============================================================================

log.info("=" * 60)
log.info("KI-Backend ready!")
log.info("Environment: %s", os.getenv("ENV", "production"))
log.info("Log Level: %s", log_level)
log.info("=" * 60)
