# -*- coding: utf-8 -*-
"""KIS-1271: Eine Stelle fuer die Admin-Authentifizierung.

Bisher stand die Pruefung viermal im Code (routes/admin_testrun.py,
routes/admin_feedback.py, routes/strategy.py, routes/metrics.py) und der
Schluessel kam ausschliesslich als Query-Parameter.

Zwei Probleme damit:

1. Sicherheit (Issue #984): Query-Parameter landen in Server-Logs,
   Proxy-Logs, Browser-Verlauf und der Shell-History. Ein Header tut das
   nicht.
2. Kodierung: Am 03.09.2026 scheiterte ein Aufruf mit einem gueltigen
   Schluessel, weil dieser ein "+" enthielt — im Query-String wird "+"
   beim Dekodieren zu einem Leerzeichen. Ein Header wird nicht so
   dekodiert und kann roh uebergeben werden.

Der Query-Parameter bleibt erhalten: bestehende Aufrufe und Lesezeichen
funktionieren weiter. Neu ist der Header X-Admin-Key, der Vorrang hat.
"""
from __future__ import annotations

import hmac
import logging
import os

from fastapi import Header, HTTPException, Query

log = logging.getLogger(__name__)

ADMIN_KEY_ENV = "STRATEGY_ADMIN_KEY"
ADMIN_KEY_HEADER = "X-Admin-Key"


def verify_admin_key(admin_key: str | None) -> None:
    """Prueft den Schluessel gegen STRATEGY_ADMIN_KEY.

    Wirft 500, wenn die Variable serverseitig fehlt — das ist ein
    Konfigurationsfehler und keine abgelehnte Anfrage. Sonst 403.
    """
    expected = os.getenv(ADMIN_KEY_ENV, "")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail=f"{ADMIN_KEY_ENV} nicht konfiguriert",
        )
    if not hmac.compare_digest(str(admin_key or ""), expected):
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")


def require_admin_key(
    admin_key: str = Query(
        "",
        description=(
            "Admin API Key. Besser: Header X-Admin-Key verwenden — "
            "Query-Parameter landen in Logs und ein '+' im Schlüssel "
            "wird hier zu einem Leerzeichen."
        ),
    ),
    x_admin_key: str = Header("", alias=ADMIN_KEY_HEADER),
) -> None:
    """FastAPI-Dependency: akzeptiert Header ODER Query-Parameter.

    Der Header hat Vorrang. Fehlt er, gilt der Query-Parameter — damit
    bleiben bestehende Aufrufe gueltig.
    """
    verify_admin_key(x_admin_key or admin_key)
