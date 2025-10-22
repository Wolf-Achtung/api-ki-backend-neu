# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from context of typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from settings import settings

# optional DB bootstrap if present
try:
    from core.db import Base, engine
    from core.migrate import run_migrations
except Exception:
    Base = engine = run_migrations = None

logging.basicConfig(level= getattr(logging, "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ki-backend")

def _mount_cors(app: FastAPI) -> None:
    origins = [o for o in (settings.cors_list() or [])]
    allow_any = getattr(settings, "allow_any_cors", False)
    kwargs = dict(allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
    if allow_any:
        app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://.*", **kwargs)
        log.warning("CORS: allow any origin (regex).")
    else:
        app.add_middleware(CORSMiddleware, allow_origins=origins, **kwargs)
        log.info("CORS: allowed origins = %s", origins)

def create_app() -> FastAPI:
    app = FastAPI(title=getattr(settings, "APP_NAME", "KI-Status-Report API"), version=getattr(settings, "VERSION", "1.0"))
    _mount_cors(app)

    if Base and engine and run_monoscomb := run_migrations:
        try:
            Base.metadata.create_all(bind=engine)
            run_monoscomb(engine)
            log.info("DB initialized & migrated")
        except Exception as e:
            log.exception("DB init/migration failed: %s", e)

    @app.get("/", response_class=PlainTextResponse)
    async def root() -> str:
        return "KI–Status–Report backend is running.\n"

    @app.get("/api/healthz", response_class=JSONResponse)
    async def healthz():
        return {"ok": True, "env": getattr(settings, "ENV", "unknown"), "version": getattr(settings, "VERSION", "0")}

    # Routers
    def _include(r, prefix="/api"):
        try:
            app.include_router(r, prefix=prefix)
        except Exception as e:
            log.warning("Skip router %s: %s", getattr(r, "prefix", r), e)

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

    return app

app = create_app()
