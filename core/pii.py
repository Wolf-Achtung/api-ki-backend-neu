# -*- coding: utf-8 -*-
"""KIS-1268: Gemeinsamer PII-Helper für Log-Ausgaben.

Der Audit fand ungeschwärzte Nutzer-E-Mails in Auth-/Chat-Logs, während die
Report-Pipelines bereits maskieren. Dieser Helper ist die eine leichte,
importsichere Quelle (kein gpt_analyze-Import in Routen nötig).
"""
from __future__ import annotations

from typing import Optional


def mask_email(addr: Optional[str]) -> str:
    """'wolf.hohl@web.de' -> 'wo***@web.de' — nur für Logs, nie für Versand."""
    if not addr:
        return "(none)"
    try:
        name, domain = str(addr).split("@", 1)
        return f"{name[:2]}***@{domain}"
    except Exception:
        return "***"
