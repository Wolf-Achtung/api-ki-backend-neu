# -*- coding: utf-8 -*-
"""services/security.py (Kompatibilitätslayer)
Re-exportiert Symbole aus core.security.
"""
from core.security import (
    TokenPayload,
    create_access_token,
    verify_access_token,
    bearer_token,
)

__all__ = [
    "TokenPayload",
    "create_access_token",
    "verify_access_token",
    "bearer_token",
]
