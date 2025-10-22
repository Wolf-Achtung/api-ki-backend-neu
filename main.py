# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from settings import settings

# Optional: keep your existing DB bootstrapping if present
try:
    from core.db import Base, engine
    from core.migrate import run_migrations
except Exception:  # pragma: no cover
    Base = engine = run_migrations = None

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ki-backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if Base and engine and run_migrations:
        try:
            Base.metadata.create_all(bind=engine)
            run_migrations(engine)
            log.info("DB initialized & migrated")
        except Exception as e:
            log.exception("DB init/migration failed: %s", e)
    yield

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)

# --- Robust CORS ---
cors_list = settings.cors_list()
cors_any = settings.CORS_ALLOW_ANY or (not cors_list and settings.ENV != "production")

cors_kwargs = dict(
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

if cors_any:
    # Accept any https/http origin (works with credentials via regex)
    app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://.*", **cors_kwargs)
    log.warning("CORS: using allow_origin_regex (any origin). Set CORS_ORIGINS to lock down in production.")
else:
    app.add_middleware(CORSMiddleware, allow_origins=cors_list, **cors_kwargs)
    log.info("CORS: allowed origins = %s", cors_list)

@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "KI–Status–Report backend is running.\n"

@app.get("/api/healthz", response_class=JSONResponse)
async def healthz():
    return {"ok": True, "env": settings.ENV, "version": settings.VERSION}

# Import and mount routers (if present)
def _include(router, prefix="/api"):
    try:
        app.include_router(router, prefix=prefix)
    except Exception as e:
        log.warning("Skipping router %s: %s", router, e)

try:
    from routes.auth import router as auth_router
    _include(auth_router, "/api")
except Exception as e:
    log.warning("Auth router not loaded: %s", e)

try:
    from routes.briefing import router as briefing_router
    _include(briefing_router, "/api")
except Exception as e:
    log.warning("Briefing router not loaded: %s", e)

try:
    from routes.analyze import router as analyze_router
    _include(analyze_router, "/api")
except Exception as e:
    log.warning("Analyze router not loaded: %s", e)

try:
    from routes.report import router as report_router
    _include(report_router, "/api")
except Exception as e:
    log.warning("Report router not loaded: %s", e)

