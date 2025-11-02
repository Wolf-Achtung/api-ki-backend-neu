# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Admin-SQL Router – deaktivierter Platzhalter
Verhindert Importfehler, wenn die App bedingt versucht, routes.admin_sql zu laden.
Alle Endpunkte sind bewusst nicht-funktional und geben enabled=False zurück.
Aktivierung NUR via ENV ADMIN_ALLOW_RAW_SQL=1 (dann bitte eine explizite Implementierung nutzen).
"""
import os
from fastapi import APIRouter

router = APIRouter(prefix="/admin-sql", tags=["admin-sql"])

ENABLED = os.getenv("ADMIN_ALLOW_RAW_SQL", "0") == "1"

@router.get("/health", include_in_schema=False)
def health():
    return {"ok": True, "enabled": ENABLED}
