# -*- coding: utf-8 -*-
from __future__ import annotations
"""routes.smoke – einfache Health/Ready-Probes"""
from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter(prefix="/smoke", tags=["smoke"], include_in_schema=False)

@router.get("/ok")
async def ok() -> JSONResponse:
    return JSONResponse({"status": "ok"})

@router.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "healthy"})

@router.get("/readyz")
async def readyz() -> JSONResponse:
    return JSONResponse({"status": "ready"})
