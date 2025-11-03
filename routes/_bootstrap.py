# file: routes/_bootstrap.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""App-Bootstrap: Security & CORS aus Settings anwenden."""
from fastapi import FastAPI
from services.security import add_security
from settings import settings

def init_app(app: FastAPI) -> None:
    add_security(app, origins=settings.cors_list(), allow_any=settings.allow_any_cors)
