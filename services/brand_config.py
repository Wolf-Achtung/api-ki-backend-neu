# -*- coding: utf-8 -*-
"""
Zentrale Branding-Konfiguration (Phase 0 Multi-Projekt).

Eine Quelle für alle marken-/personenbezogenen Angaben, die bisher in den
Report-Templates, Prompts und E-Mails hardcodiert waren. Auflösung je Key:

  1. ENV ``BRAND_<KEY>`` (z. B. BRAND_ADVISOR_NAME)
  2. JSON-Datei unter ``BRAND_CONFIG_PATH`` (Default: config/brand.json)
  3. eingebaute Defaults (= heutiges Branding KI-Sicherheit.jetzt)

Bestehende ENV-Variablen (OWNER_NAME, CONTACT_EMAIL, SITE_URL) werden aus
Kompatibilitätsgründen weiterhin berücksichtigt.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger(__name__)

# Defaults = aktuelles Branding. Ein neues Projekt überschreibt per
# brand.json oder BRAND_*-ENV, ohne dass Templates angefasst werden müssen.
_DEFAULTS: Dict[str, str] = {
    "brand_name": "KI-Sicherheit.jetzt",
    "claim": "Ihr Partner für KI-Readiness",
    "advisor_name": "Wolf Hohl",
    "advisor_title": "TÜV-zertifizierter KI-Manager",
    "advisor_signature": "Wolf Hohl · TÜV-zertifizierter KI-Manager",
    "advisor_bio": (
        "TÜV-zertifizierter KI-Manager mit 30 Jahren Beratungserfahrung "
        "in Marketing und Kommunikation"
    ),
    "contact_email": "kontakt@ki-sicherheit.jetzt",
    "site_url": "https://ki-sicherheit.jetzt",
    "app_url": "https://make.ki-sicherheit.jetzt",
    "feedback_url": "https://make.ki-sicherheit.jetzt/feedback/feedback.html",
    "privacy_url": "https://ki-sicherheit.jetzt/datenschutz",
    "logo_small": "ki-sicherheit-logo-small.png",
    "logo_alt": "KI-Sicherheit.jetzt",
    "cert_logo": "tuev-logo-transparent.png",
    "cert_logo_alt": "TÜV Austria zertifiziert",
}

# Kompatibilität: bestehende ENV-Namen → Brand-Keys
_LEGACY_ENV: Dict[str, str] = {
    "advisor_name": "OWNER_NAME",
    "contact_email": "CONTACT_EMAIL",
    "site_url": "SITE_URL",
}


def _load_file() -> Dict[str, Any]:
    path = os.getenv("BRAND_CONFIG_PATH", "config/brand.json")
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / p
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # noqa: BLE001 - Branding darf Rendern nie brechen
        log.warning("brand_config: %s nicht lesbar (%s) — nutze Defaults", p, exc)
        return {}


@lru_cache(maxsize=1)
def get_brand() -> Dict[str, str]:
    """Aufgelöstes Branding als flaches Dict (immer alle Keys vorhanden)."""
    file_cfg = _load_file()
    brand: Dict[str, str] = {}
    for key, default in _DEFAULTS.items():
        value = os.getenv(f"BRAND_{key.upper()}")
        if not value and key in _LEGACY_ENV:
            value = os.getenv(_LEGACY_ENV[key])
        if not value:
            value = file_cfg.get(key)
        brand[key] = str(value) if value else default
    return brand


def reset_cache() -> None:
    """Nur für Tests: Cache invalidieren."""
    get_brand.cache_clear()
