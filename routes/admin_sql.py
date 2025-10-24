# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Try to reuse the app's engine if available
try:
    from core.db import engine as _engine  # type: ignore
except Exception:
    _engine = None

from core.sql_hotfixes import HOTFIXES

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin-sql"])

ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN", "")
ALLOW_RAW_SQL = os.getenv("ADMIN_ALLOW_RAW_SQL", "0") == "1"

def _get_engine() -> Engine:
    if _engine is not None:
        return _engine
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("PGDATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not configured")
    return create_engine(url, pool_pre_ping=True, future=True)

class HotfixRequest(BaseModel):
    name: str = Field(..., description="Name des Hotfix-Skripts, z.B. 'login_codes_reports_v1'")
    statement_timeout_ms: int = Field(30000, ge=1000, le=300000)

class RawSQLRequest(BaseModel):
    sql: str = Field(..., description="Kompletter SQL-Text (DDL/DML); idempotent ausführen.")
    statement_timeout_ms: int = Field(30000, ge=1000, le=300000)

def _require_admin_token(x_admin_token: Optional[str]) -> None:
    if not ADMIN_API_TOKEN:
        raise HTTPException(status_code=500, detail="ADMIN_API_TOKEN not configured on server")
    if not x_admin_token or x_admin_token.strip() != ADMIN_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/apply-hotfix")
def apply_hotfix(req: HotfixRequest, x_admin_token: Optional[str] = Header(None)) -> dict:
    _require_admin_token(x_admin_token)
    sql = HOTFIXES.get(req.name)
    if not sql:
        raise HTTPException(status_code=404, detail=f"Unknown hotfix '{req.name}'")
    eng = _get_engine()
    started = time.perf_counter()
    with eng.begin() as conn:
        # set local statement_timeout
        conn.exec_driver_sql(f"SET LOCAL statement_timeout = {int(req.statement_timeout_ms)}")
        conn.exec_driver_sql(sql)
    dur_ms = int((time.perf_counter() - started) * 1000)
    log.info("ADMIN_HOTFIX applied: %s in %d ms", req.name, dur_ms)
    return {"ok": True, "name": req.name, "duration_ms": dur_ms}

@router.post("/run-sql")
def run_sql(req: RawSQLRequest, x_admin_token: Optional[str] = Header(None)) -> dict:
    # For safety we require explicit opt-in via env var
    if not ALLOW_RAW_SQL:
        raise HTTPException(status_code=403, detail="Raw SQL disabled; set ADMIN_ALLOW_RAW_SQL=1 to enable")
    _require_admin_token(x_admin_token)
    eng = _get_engine()
    started = time.perf_counter()
    with eng.begin() as conn:
        conn.exec_driver_sql(f"SET LOCAL statement_timeout = {int(req.statement_timeout_ms)}")
        conn.exec_driver_sql(req.sql)
    dur_ms = int((time.perf_counter() - started) * 1000)
    log.warning("ADMIN_RAW_SQL executed in %d ms", dur_ms)
    return {"ok": True, "duration_ms": dur_ms}