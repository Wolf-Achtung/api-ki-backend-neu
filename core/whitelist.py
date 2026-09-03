# -*- coding: utf-8 -*-
"""
core.whitelist — Single source of truth for the test-phase E-Mail-Whitelist.

Imported by routes/auth.py (gate /auth/request-code) and by report-pipeline
endpoints that need to verify the JWT subject is allowed to trigger LLM work.
Keep the canonical list here; do not duplicate it elsewhere.

KIS-1264: Zusaetzliche Adressen kommen aus der ENV-Variablen
EXTRA_WHITELIST (kommagetrennt). Damit laesst sich jemand freischalten,
ohne Code zu aendern und ohne Deploy — ein Backend-Deploy bricht laufende
Report-Generierungen ab, das soll eine Freischaltung nicht kosten.
Admin-Rechte bleiben bewusst code-only: sie sind eine Sicherheitsgrenze
und keine Betriebseinstellung.
"""
from __future__ import annotations

import logging
import os

from fastapi import HTTPException, status

log = logging.getLogger(__name__)

EXTRA_WHITELIST_ENV = "EXTRA_WHITELIST"

# Canonical whitelist. Synchron mit setup_database.py TESTUSERS halten.
# Alle Adressen werden case-insensitive verglichen (lower).
EMAIL_WHITELIST: frozenset[str] = frozenset(
    email.lower()
    for email in [
        "j.hohl@freenet.de",
        "kerstin.geffert@gmail.com",
        "daniel.effinger@web.de",
        "post@zero2.de",
        "giselapeter@peter-partner.de",
        "wolf.hohl@web.de",
        "jan.bonath@white-spot-films.com",
        "jbfilm@outlook.de",
        "mail@ennoreese.de",
        "geffertj@mac.com",
        "geffertkilian@gmail.com",
        "berndemhart46@gmail.com",
        "po@wbs-slg.de",
        "trailerman01@outlook.de",
        "hilfe@ki-sicherheit.jetzt",
        "levent.graef@posteo.de",
        "birgit.cook@ulitzka-partner.de",
        "alexander.luckow@icloud.com",
        "frank.beer@kabelmail.de",
        "patrick@silk-relations.com",
        "marc@trailerhaus-onair.de",
        "matthias@trailerhaus-onair.de",
        "norbert@trailerhaus.de",
        "michelmorales@me.com",
        "sonia-souto@mac.com",
        "christian.ulitzka@ulitzka-partner.de",
        "srack@gmx.net",
        "buss@maria-hilft.de",
        "w.beestermoeller@web.de",
        "bewertung@ki-sicherheit.jetzt",  # Admin
        "test@example.com",  # CI/CD
        "test-v7-final@ki-sicherheit.jetzt",
        "test-v7-1@ki-sicherheit.jetzt",
        "test-v7-400@ki-sicherheit.jetzt",
    ]
)

# Admin-Mails (Untermenge der Whitelist) — wer Cancel/List-Endpoints nutzen darf.
ADMIN_EMAILS: frozenset[str] = frozenset({"bewertung@ki-sicherheit.jetzt"})


_zuletzt_geloggt: frozenset[str] | None = None


def _extra_whitelist() -> frozenset[str]:
    """Adressen aus EXTRA_WHITELIST (kommagetrennt, case-insensitive).

    Bewusst bei jedem Aufruf frisch gelesen statt beim Import: Der Login
    ist kein heisser Pfad, und ein Cache wuerde nach einer ENV-Aenderung
    einen alten Stand festhalten. Eintraege ohne "@" werden verworfen —
    ein Tippfehler soll nicht still zu einem toten Eintrag werden.
    """
    global _zuletzt_geloggt

    roh = os.getenv(EXTRA_WHITELIST_ENV, "") or ""
    eintraege = [e.strip().lower() for e in roh.split(",")]
    gueltig = frozenset(e for e in eintraege if e and "@" in e)
    verworfen = [e for e in eintraege if e and "@" not in e]

    if gueltig != _zuletzt_geloggt:
        _zuletzt_geloggt = gueltig
        if gueltig:
            log.info("[WHITELIST] %d Adresse(n) aus %s übernommen",
                     len(gueltig), EXTRA_WHITELIST_ENV)
        if verworfen:
            log.warning("[WHITELIST] %d Eintrag/Einträge in %s ohne '@' ignoriert: %s",
                        len(verworfen), EXTRA_WHITELIST_ENV, ", ".join(verworfen))
    return gueltig


def all_whitelisted() -> frozenset[str]:
    """Wirksame Whitelist: fester Code-Bestand plus ENV-Ergänzungen."""
    return EMAIL_WHITELIST | _extra_whitelist()


def is_whitelisted(email: str | None) -> bool:
    """Return True iff the given email is in the test-phase whitelist."""
    if not email:
        return False
    return email.strip().lower() in all_whitelisted()


def require_whitelisted(email: str | None) -> str:
    """
    Raise HTTPException 403 if the email is not whitelisted.
    Returns the normalised (lowercased, stripped) email on success.
    """
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Diese E-Mail-Adresse ist nicht für die Testphase freigeschaltet.",
        )
    normalised = email.strip().lower()
    if normalised not in all_whitelisted():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Diese E-Mail-Adresse ist nicht für die Testphase freigeschaltet.",
        )
    return normalised


def is_admin(email: str | None) -> bool:
    """Return True iff the given email is an admin."""
    if not email:
        return False
    return email.strip().lower() in ADMIN_EMAILS
