# -*- coding: utf-8 -*-
from __future__ import annotations

"""
routes.smoke – lightweight health/smoke router
- Fixes: ImportError in startup when module is missing.
- Provides: /api/smoke/ok, /api/smoke/healthz, /api/smoke/readyz
- Hidden from OpenAPI (include_in_schema=False).
"""

from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter(prefix="/smoke", tags=["smoke"], include_in_schema=False)

@router.get("/ok")
async def ok() -> JSONResponse:
    return JSONResponse({"status": "ok"})

@router.get("/healthz")
async def healthz() -> JSONResponse:
    # app-level checks can be added here later (db ping, cache, etc.)
    return JSONResponse({"status": "healthy"})

@router.get("/readyz")
async def readyz() -> JSONResponse:
    # readiness can be extended to check background workers, etc.
    return JSONResponse({"status": "ready"})
