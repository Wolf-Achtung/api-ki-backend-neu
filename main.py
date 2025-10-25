
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

allowed = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()]
if not allowed and os.getenv("CORS_ALLOW_ANY", "0") == "1":
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    log.warning("CORS: allow all (development)")
else:
    app.add_middleware(CORSMiddleware, allow_origins=allowed or ["https://make.ki-sicherheit.jetzt"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    log.info("CORS: allowed origins = %s", allowed or ["https://make.ki-sicherheit.jetzt"])

def _mount(router_path: str, prefix: str, name: str) -> None:
    try:
        module = __import__(router_path, fromlist=["router"])
        app.include_router(module.router, prefix=prefix)
        log.info("Mounted router: %s", f"{prefix}/{name}".rstrip("/"))
    except Exception as exc:
        log.warning("Router %s not loaded: %s", router_path, exc)

# bekannte Router
_mount("routes.auth", "/api", "auth")
_mount("routes.analyze", "/api", "analyze")
_mount("routes.report", "/api", "report")
_mount("routes.admin_sql", "", "api/admin (sql)")
# NEU: Briefings (Draft + Latest + Async Submit)
_mount("routes.briefings", "/api", "briefings")

@app.get("/api/healthz")
def healthz():
    return {"ok": True}
