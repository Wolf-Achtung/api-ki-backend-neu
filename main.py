# -*- coding: utf-8 -*-
"""FastAPI entrypoint for KI Status Report – Stufe DE/i18n-ready.
- CORS from settings
- Health/diag
- Routers: briefing (submit), analyze (HTML), report (PDF)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from settings import settings

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ki-backend")

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "KI–Status–Report backend is running.\n"

@app.get("/api/healthz", response_class=JSONResponse)
async def healthz():
    return {
        "ok": True,
        "time": datetime.now(timezone.utc).isoformat(),
        "env": settings.ENV,
        "version": settings.VERSION,
        "pdf_service": bool(settings.PDF_SERVICE_URL),
        "status": "ok",
    }

@app.get("/api/diag", response_class=JSONResponse)
async def diag():
    return {
        "ok": True,
        "settings": {
                "APP_NAME": settings.APP_NAME,
                "ENV": settings.ENV,
                "VERSION": settings.VERSION,
                "PDF_SERVICE_URL_SET": bool(settings.PDF_SERVICE_URL),
                "PDF_TIMEOUT_MS": settings.PDF_TIMEOUT_MS,
                "DEBUG": settings.LOG_LEVEL.upper() in {"DEBUG","TRACE"},
            },
        "time": datetime.now(timezone.utc).isoformat(),
    }

# Routers
from routes.briefing import router as briefing_router
from routes.analyze import router as analyze_router
from routes.report import router as report_router

app.include_router(briefing_router, prefix="/api")
app.include_router(analyze_router,  prefix="/api")
app.include_router(report_router,   prefix="/api")
