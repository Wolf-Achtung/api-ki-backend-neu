# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ki-backend")

app = FastAPI(title="KI Backend")

# CORS – erlaubt bekannte Frontends; REGEX-Fallback ist optional
allowed = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()]
if not allowed and os.getenv("CORS_ALLOW_ANY", "0") == "1":
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])
    log.warning("CORS: allow all (development)")
else:
    app.add_middleware(CORSMiddleware, allow_origins=allowed or ["https://make.ki-sicherheit.jetzt"],
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    log.info("CORS: allowed origins = %s", allowed or ["https://make.ki-sicherheit.jetzt"])

# Mount existing routers (falls dein Projekt andere Pfade nutzt, bleibt dies folgenlos)
try:
    from routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/api")
    log.info("Mounted router: /api/auth")
except Exception as exc:
    log.warning("Router routes.auth not loaded: %s", exc)

try:
    from routes.analyze import router as analyze_router
    app.include_router(analyze_router, prefix="/api")
    log.info("Mounted router: /api/analyze")
except Exception as exc:
    log.warning("Router routes.analyze not loaded: %s", exc)

try:
    from routes.report import router as report_router
    app.include_router(report_router, prefix="/api")
    log.info("Mounted router: /api/report")
except Exception as exc:
    log.warning("Router routes.report not loaded: %s", exc)

# NEW: Admin SQL router
try:
    from routes.admin_sql import router as admin_sql_router
    app.include_router(admin_sql_router)
    log.info("Mounted router: /api/admin (sql)")
except Exception as exc:
    log.warning("Router routes.admin_sql not loaded: %s", exc)

@app.get("/api/healthz")
def healthz():
    return {"ok": True}