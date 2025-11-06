# file: routes/favicon.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Response

router = APIRouter(tags=["assets"])

@router.get("/favicon.ico")
def favicon() -> Response:
    # Intentionally return 204 (no icon), avoids 404 noise in logs.
    return Response(status_code=204)
