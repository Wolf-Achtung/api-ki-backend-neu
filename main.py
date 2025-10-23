# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from settings import settings

# Optional DB bootstrap
try:
    from core.db import Base, engine
    from core.migrate import run_migrations
except Exception:
    Base = None
    engine = None
    run_migrations = None

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ki-backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if Base and engine:
        try:
            Base.metadata.create_all(bind=engine)
            if callable(run_migrations):
                run_migrations(engine)
            log.info("DB initialized & migrated")
        except Exception as e:
            log.exception("DB init/migration failed: %s", e)
    yield

app = FastAPI(title=getattr(settings, "APP_NAME", "KI-Status-Report API"),
              version=getattr(settings, "VERSION", "1.0.0"),
              lifespan=lifespan)

# CORS
origins = []
try:
    origins = settings.cors_list()
except Exception:
    raw = getattr(settings, "CORS_ORIGINS", "") or ""
    origins = [s.strip().rstrip("/") for s in raw.split(",") if s.strip()]
allow_any = False
try:
    allow_any = settings.allow_any_cors
except Exception:
    allow_any = False
kwargs = dict(allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
if allow_any:
    app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://.*", **kwargs)
    log.warning("CORS: using allow_origin_regex (any origin). Set CORS_ORIGINS to lock down in production.")
else:
    app.add_middleware(CORSMiddleware, allow_origins=origins, **kwargs)
    log.info("CORS: allowed origins = %s", origins)

# Health
@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "KI–Status–Report backend is running.\n"

@app.get("/api/healthz", response_class=JSONResponse)
async def healthz():
    return {"OK": True, "env": getattr(settings, "ENV", "unknown"), "version": getattr(settings, "VERSION", "0")}

# Routers
def include_router_safe(module_path: str, attr: str, prefix: str = "/api"):
    try:
        mod = __import__(module_path, fromlist=[attr])
        router = getattr(mod, "router")
        app.include_router(router, prefix=prefix)
        log.info("Mounted router: %s%s", prefix, getattr(router, "prefix", ""))
    except Exception as e:
        log.warning("Router %s not loaded: %s", module_path, e)

include_router_safe("routes.auth", "router")
include_router_safe("routes.briefing", "router")
include_router_safe("routes.analyze", "router")
include_router_safe("routes.report", "router")
# NEU: Drafts (Resume-Funktion) – optional vorhanden
include_router_safe("routes.briefing_drafts", "router")
