# file: services/security.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Security-Middleware: CORS strikt, Security-Header, Request-ID.
Warum: Minimiert Angriffsfläche, bessere Auditierbarkeit."""
from typing import Callable
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware

def add_security(app: FastAPI, *, origins: list[str], allow_any: bool) -> None:
    if allow_any:
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                           allow_methods=["*"], allow_headers=["*"])
    else:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                           allow_methods=["GET","POST","OPTIONS"], allow_headers=["Authorization","Content-Type","Accept"])

    @app.middleware("http")
    async def _security_headers(request: Request, call_next: Callable):
        rid = request.headers.get("X-Request-ID") or uuid4().hex[:12]  # warum: Tracing/Korrelation
        response: Response = await call_next(request)
        response.headers.setdefault("X-Request-ID", rid)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        return response
