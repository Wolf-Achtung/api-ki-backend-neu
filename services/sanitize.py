# -*- coding: utf-8 -*-
"""Utility functions for safe UTF-8 handling.

This module centralizes string sanitization to avoid Mojibake (e.g. "FragebÃ¶gen").
It normalizes to NFC and guarantees UTF-8 output for any value.
"""
from __future__ import annotations

import json
import unicodedata
from typing import Any

def ensure_utf8(value: Any) -> str:
    """Return a UTF-8 safe string representation with NFC normalization.

    - Converts non-str values using ``json.dumps(..., ensure_ascii=False)`` to
      preserve Umlauts and special characters.
    - Normalizes Unicode to NFC to avoid accent/combining character issues.
    """
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            s = value.decode("utf-8", errors="replace")
        except Exception:
            s = value.decode("latin-1", errors="replace")
        return unicodedata.normalize("NFC", s)
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    try:
        s = json.dumps(value, ensure_ascii=False)
        return unicodedata.normalize("NFC", s)
    except Exception:
        return unicodedata.normalize("NFC", str(value))
