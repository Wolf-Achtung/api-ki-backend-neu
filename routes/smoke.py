# file: routes/smoke.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Response

router = APIRouter(prefix="/smoke", tags=["health"])

@router.get("")
def smoke(_: Response):
    now = datetime.now(timezone.utc).isoformat()
    return {"ok": True, "ts": now, "service": "ki-backend", "endpoint": "smoke"}
