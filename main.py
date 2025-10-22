# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from settings import settings
from core.db import Base, engine
from core.migrate import run_migrations

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ki-backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        run_migrations(engine)
        logger.info("DB initialized & migrated")
    except Exception as e:
        logger.exception("DB init/migration failed: %s", e)
    yield

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(settings.cors_origins or ["*"] if settings.ENV != "production" else settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "KI–Status–Report backend is running.\n"

@app.get("/api/healthz", response_class=JSONResponse)
async def healthz():
    return {"ok": True, "env": settings.ENV, "version": settings.VERSION}

from routes.auth import router as auth_router
from routes.briefing import router as briefing_router
from routes.analyze import router as analyze_router
from routes.report import router as report_router
from routes.admin import router as admin_router

app.include_router(auth_router, prefix="/api")
app.include_router(briefing_router, prefix="/api")
app.include_router(analyze_router,  prefix="/api")
app.include_router(report_router,   prefix="/api")
app.include_router(admin_router,    prefix="/api")
