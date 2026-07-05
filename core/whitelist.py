# -*- coding: utf-8 -*-
"""
core.whitelist — Single source of truth for the test-phase E-Mail-Whitelist.

Imported by routes/auth.py (gate /auth/request-code) and by report-pipeline
endpoints that need to verify the JWT subject is allowed to trigger LLM work.
Keep the canonical list here; do not duplicate it elsewhere.
"""
from __future__ import annotations

from fastapi import HTTPException, status

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


def is_whitelisted(email: str | None) -> bool:
    """Return True iff the given email is in the test-phase whitelist."""
    if not email:
        return False
    return email.strip().lower() in EMAIL_WHITELIST


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
    if normalised not in EMAIL_WHITELIST:
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
